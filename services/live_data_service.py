"""
Live Data Service — Fetches trending data from free external APIs.
Each fetcher returns a list of dicts matching Trend model fields.

Supported sources:
- Google Trends (pytrends)
- Stocks (yfinance)
- News (GNews API)
- YouTube (RSS feed)
- Music (Last.fm API)
"""

import logging
import hashlib
from django.conf import settings

logger = logging.getLogger(__name__)


def _make_source_id(source, identifier):
    """Generate a unique source_id for deduplication."""
    raw = f"{source}:{identifier}"
    return hashlib.md5(raw.encode()).hexdigest()


def _score_from_value(value, max_value=100):
    """Normalize a value to a 0-100 score."""
    if max_value <= 0:
        return 50.0
    return round(min(value / max_value * 100, 100), 1)


def _classify_velocity(score):
    """Classify velocity based on score."""
    if score >= 85:
        return 'exploding'
    elif score >= 60:
        return 'rising'
    elif score >= 30:
        return 'steady'
    return 'declining'


# ═══════════════════════════════════════════════════════
# Google Trends
# ═══════════════════════════════════════════════════════

class GoogleTrendsFetcher:
    """Fetch trending searches from Google Trends via pytrends."""

    @staticmethod
    def fetch(geo='united_states', count=20):
        trends = []
        try:
            from pytrends.request import TrendReq

            pytrends = TrendReq(hl='en-US', tz=360)
            trending_df = pytrends.trending_searches(pn=geo)

            for idx, row in trending_df.head(count).iterrows():
                title = str(row[0]).strip()
                if not title:
                    continue

                score = round(95 - idx * 3.5, 1)
                score = max(score, 20)

                trends.append({
                    'title': title,
                    'category': 'other',
                    'platform': 'twitter',
                    'description': f'"{title}" is currently trending on Google Search. This topic is generating significant search interest and social media discussion across platforms.',
                    'score': score,
                    'velocity': _classify_velocity(score),
                    'likes': 0,
                    'shares': 0,
                    'comments': 0,
                    'source': 'google_trends',
                    'external_url': f'https://trends.google.com/trends/explore?q={title.replace(" ", "+")}',
                    'source_id': _make_source_id('google_trends', title.lower()),
                })

            logger.info(f"GoogleTrends: fetched {len(trends)} trends")
        except ImportError:
            logger.warning("pytrends not installed. Run: pip install pytrends")
        except Exception as e:
            logger.error(f"GoogleTrends error: {e}")

        return trends


# ═══════════════════════════════════════════════════════
# Stock Market
# ═══════════════════════════════════════════════════════

class StockTrendsFetcher:
    """Fetch trending stock movers via yfinance."""

    WATCHLIST = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA',
        'BRK-B', 'JPM', 'V', 'JNJ', 'WMT', 'PG', 'MA', 'UNH',
        'HD', 'DIS', 'NFLX', 'PYPL', 'AMD', 'INTC', 'CRM', 'ORCL', 'CSCO',
    ]

    @staticmethod
    def fetch(count=15):
        trends = []
        try:
            import yfinance as yf

            tickers = yf.Tickers(' '.join(StockTrendsFetcher.WATCHLIST))

            movers = []
            for symbol in StockTrendsFetcher.WATCHLIST:
                try:
                    ticker = tickers.tickers.get(symbol)
                    if not ticker:
                        continue
                    info = ticker.fast_info
                    price = getattr(info, 'last_price', 0) or 0
                    prev_close = getattr(info, 'previous_close', 0) or 0
                    if prev_close > 0:
                        change_pct = ((price - prev_close) / prev_close) * 100
                    else:
                        change_pct = 0
                    market_cap = getattr(info, 'market_cap', 0) or 0
                    movers.append({
                        'symbol': symbol,
                        'price': price,
                        'change_pct': change_pct,
                        'market_cap': market_cap,
                    })
                except Exception:
                    continue

            # Sort by absolute change percentage
            movers.sort(key=lambda x: abs(x['change_pct']), reverse=True)

            for idx, m in enumerate(movers[:count]):
                change = m['change_pct']
                direction = "📈 up" if change > 0 else "📉 down"
                score = min(abs(change) * 15 + 40, 99)

                if change > 3:
                    velocity = 'exploding'
                elif change > 0:
                    velocity = 'rising'
                elif change > -2:
                    velocity = 'steady'
                else:
                    velocity = 'declining'

                trends.append({
                    'title': f'{m["symbol"]} {direction} {abs(change):.1f}% — ${m["price"]:.2f}',
                    'category': 'business',
                    'platform': 'twitter',
                    'description': f'{m["symbol"]} stock is {direction} {abs(change):.1f}% today, trading at ${m["price"]:.2f}. '
                                   f'Market cap: ${m["market_cap"]/1e9:.1f}B. '
                                   f'This move is generating discussion across financial communities.',
                    'score': round(score, 1),
                    'velocity': velocity,
                    'likes': 0,
                    'shares': 0,
                    'comments': 0,
                    'source': 'stocks',
                    'external_url': f'https://finance.yahoo.com/quote/{m["symbol"]}/',
                    'source_id': _make_source_id('stocks', m['symbol']),
                })

            logger.info(f"Stocks: fetched {len(trends)} movers")
        except ImportError:
            logger.warning("yfinance not installed. Run: pip install yfinance")
        except Exception as e:
            logger.error(f"Stocks error: {e}")

        return trends


# ═══════════════════════════════════════════════════════
# News Headlines
# ═══════════════════════════════════════════════════════

class NewsTrendsFetcher:
    """Fetch trending news via GNews API (free: 100 req/day)."""

    @staticmethod
    def fetch(count=15):
        trends = []
        api_key = getattr(settings, 'GNEWS_API_KEY', '')
        if not api_key:
            logger.info("GNews: no API key set, using fallback RSS")
            return NewsTrendsFetcher._fetch_rss_fallback(count)

        try:
            import requests

            url = f'https://gnews.io/api/v4/top-headlines?category=general&lang=en&max={count}&apikey={api_key}'
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            for idx, article in enumerate(data.get('articles', [])[:count]):
                title = article.get('title', '').strip()
                desc = article.get('description', '') or ''
                source_name = article.get('source', {}).get('name', 'News')
                article_url = article.get('url', '')

                score = round(90 - idx * 3, 1)
                score = max(score, 25)

                trends.append({
                    'title': title,
                    'category': 'other',
                    'platform': 'twitter',
                    'description': f'[{source_name}] {desc}' if desc else f'Breaking news from {source_name}.',
                    'score': score,
                    'velocity': _classify_velocity(score),
                    'likes': 0,
                    'shares': 0,
                    'comments': 0,
                    'source': 'news',
                    'external_url': article_url,
                    'source_id': _make_source_id('news', title.lower()[:100]),
                })

            logger.info(f"News (GNews): fetched {len(trends)} articles")
        except Exception as e:
            logger.error(f"News error: {e}")
            return NewsTrendsFetcher._fetch_rss_fallback(count)

        return trends

    @staticmethod
    def _fetch_rss_fallback(count=10):
        """Fallback: fetch Google News RSS (no key needed)."""
        trends = []
        try:
            import feedparser

            feed = feedparser.parse('https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en')

            for idx, entry in enumerate(feed.entries[:count]):
                title = entry.get('title', '').strip()
                link = entry.get('link', '')
                summary = entry.get('summary', '')

                score = round(88 - idx * 4, 1)
                score = max(score, 20)

                trends.append({
                    'title': title,
                    'category': 'other',
                    'platform': 'twitter',
                    'description': summary[:300] if summary else f'Top news story trending across platforms.',
                    'score': score,
                    'velocity': _classify_velocity(score),
                    'likes': 0,
                    'shares': 0,
                    'comments': 0,
                    'source': 'news',
                    'external_url': link,
                    'source_id': _make_source_id('news', title.lower()[:100]),
                })

            logger.info(f"News (RSS fallback): fetched {len(trends)} articles")
        except Exception as e:
            logger.error(f"News RSS error: {e}")

        return trends


# ═══════════════════════════════════════════════════════
# YouTube Trending
# ═══════════════════════════════════════════════════════

class YouTubeTrendsFetcher:
    """Fetch trending YouTube videos via RSS feeds."""

    @staticmethod
    def fetch(count=15):
        trends = []
        try:
            import feedparser

            # YouTube trending RSS via Invidious (public instance)
            feed_urls = [
                'https://www.youtube.com/feeds/videos.xml?channel_id=UCYfdidRxbB8Qhf0Nx7ioOYw',  # YouTube Trending/News
            ]

            # Use Google News YouTube section as fallback for trending
            feed = feedparser.parse('https://news.google.com/rss/search?q=site:youtube.com+trending&hl=en-US&gl=US&ceid=US:en')

            for idx, entry in enumerate(feed.entries[:count]):
                title = entry.get('title', '').strip()
                link = entry.get('link', '')
                summary = entry.get('summary', '')

                score = round(85 - idx * 3.5, 1)
                score = max(score, 20)

                trends.append({
                    'title': title,
                    'category': 'entertainment',
                    'platform': 'youtube',
                    'description': summary[:300] if summary else f'This video is trending on YouTube with significant viewer engagement.',
                    'score': score,
                    'velocity': _classify_velocity(score),
                    'likes': 0,
                    'shares': 0,
                    'comments': 0,
                    'source': 'youtube',
                    'external_url': link,
                    'source_id': _make_source_id('youtube', title.lower()[:100]),
                })

            logger.info(f"YouTube: fetched {len(trends)} videos")
        except ImportError:
            logger.warning("feedparser not installed. Run: pip install feedparser")
        except Exception as e:
            logger.error(f"YouTube error: {e}")

        return trends


# ═══════════════════════════════════════════════════════
# Music Trends
# ═══════════════════════════════════════════════════════

class MusicTrendsFetcher:
    """Fetch trending music via Last.fm API (free)."""

    @staticmethod
    def fetch(count=15):
        trends = []
        api_key = getattr(settings, 'LASTFM_API_KEY', '')

        if not api_key:
            logger.info("Last.fm: no API key, using RSS fallback")
            return MusicTrendsFetcher._fetch_rss_fallback(count)

        try:
            import requests

            url = f'https://ws.audioscrobbler.com/2.0/?method=chart.gettoptracks&api_key={api_key}&format=json&limit={count}'
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            tracks = data.get('tracks', {}).get('track', [])
            for idx, track in enumerate(tracks[:count]):
                name = track.get('name', '')
                artist = track.get('artist', {}).get('name', 'Unknown')
                listeners = int(track.get('listeners', 0))
                playcount = int(track.get('playcount', 0))
                track_url = track.get('url', '')

                score = _score_from_value(listeners, max_value=5000000)
                score = max(score, 20)

                trends.append({
                    'title': f'🎵 {name} — {artist}',
                    'category': 'music',
                    'platform': 'tiktok',
                    'description': f'"{name}" by {artist} is trending in global music charts. '
                                   f'{listeners:,} listeners, {playcount:,} plays. '
                                   f'This track is driving engagement across streaming and social platforms.',
                    'score': round(score, 1),
                    'velocity': _classify_velocity(score),
                    'likes': listeners,
                    'shares': playcount // 10,
                    'comments': playcount // 50,
                    'source': 'music',
                    'external_url': track_url,
                    'source_id': _make_source_id('music', f'{artist}:{name}'.lower()),
                })

            logger.info(f"Music (Last.fm): fetched {len(trends)} tracks")
        except Exception as e:
            logger.error(f"Music error: {e}")
            return MusicTrendsFetcher._fetch_rss_fallback(count)

        return trends

    @staticmethod
    def _fetch_rss_fallback(count=10):
        """Fallback: fetch music news via RSS."""
        trends = []
        try:
            import feedparser

            feed = feedparser.parse('https://news.google.com/rss/search?q=trending+music+charts&hl=en-US&gl=US&ceid=US:en')

            for idx, entry in enumerate(feed.entries[:count]):
                title = entry.get('title', '').strip()
                link = entry.get('link', '')

                score = round(80 - idx * 4, 1)
                score = max(score, 20)

                trends.append({
                    'title': f'🎵 {title}',
                    'category': 'music',
                    'platform': 'tiktok',
                    'description': f'Music trend: {title}',
                    'score': score,
                    'velocity': _classify_velocity(score),
                    'likes': 0,
                    'shares': 0,
                    'comments': 0,
                    'source': 'music',
                    'external_url': link,
                    'source_id': _make_source_id('music', title.lower()[:100]),
                })

            logger.info(f"Music (RSS fallback): fetched {len(trends)} items")
        except Exception as e:
            logger.error(f"Music RSS error: {e}")

        return trends


# ═══════════════════════════════════════════════════════
# Master Fetcher
# ═══════════════════════════════════════════════════════

FETCHERS = {
    'google_trends': GoogleTrendsFetcher,
    'stocks': StockTrendsFetcher,
    'news': NewsTrendsFetcher,
    'youtube': YouTubeTrendsFetcher,
    'music': MusicTrendsFetcher,
}


def fetch_all_live_trends(sources=None):
    """
    Fetch trends from all (or specified) sources.
    Returns a dict of {source_name: [trend_dicts]}.
    """
    if sources is None:
        sources = list(FETCHERS.keys())

    results = {}
    for source in sources:
        fetcher = FETCHERS.get(source)
        if fetcher:
            try:
                results[source] = fetcher.fetch()
            except Exception as e:
                logger.error(f"Error fetching {source}: {e}")
                results[source] = []
        else:
            logger.warning(f"Unknown source: {source}")

    return results
