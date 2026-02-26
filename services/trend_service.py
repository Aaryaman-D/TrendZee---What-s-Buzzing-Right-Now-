from django.db.models import Q
from trends.models import Trend


class TrendService:

    @staticmethod
    def get_top_trends(limit=10):
        """Return top trending items by score."""
        return Trend.objects.order_by('-score')[:limit]

    @staticmethod
    def get_filtered_trends(category='', search='', platform='', source=''):
        """Return filtered trends based on query params."""
        qs = Trend.objects.all()

        if category:
            qs = qs.filter(category=category)

        if platform:
            qs = qs.filter(platform=platform)

        if source:
            qs = qs.filter(source=source)

        if search:
            qs = qs.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )

        return qs.order_by('-score')

    @staticmethod
    def get_trend_by_id(pk):
        """Fetch a single trend by ID."""
        try:
            return Trend.objects.get(pk=pk)
        except Trend.DoesNotExist:
            return None

    @staticmethod
    def get_related_trends(trend, limit=5):
        """Return related trends by category, excluding the current one."""
        return Trend.objects.filter(
            category=trend.category
        ).exclude(pk=trend.pk).order_by('-score')[:limit]

    @staticmethod
    def search_trends_for_context(keywords, limit=5):
        """
        Search trends by keyword list - used for chatbot context injection.
        Returns top matching trends as plain dicts for AI context.
        """
        if not keywords:
            return []

        query = Q()
        for kw in keywords:
            query |= Q(title__icontains=kw) | Q(description__icontains=kw) | Q(category__icontains=kw)

        trends = Trend.objects.filter(query).order_by('-score')[:limit]
        return [
            {
                'title': t.title,
                'category': t.category,
                'platform': t.platform,
                'description': t.description[:300],
                'score': t.score,
                'velocity': t.velocity,
                'likes': t.likes,
                'shares': t.shares,
                'comments': t.comments,
            }
            for t in trends
        ]

    @staticmethod
    def extract_trend_keywords(question):
        """
        Simple keyword extraction from user question.
        Can be replaced with NLP in production.
        """
        trend_terms = [
            'trend', 'trending', 'viral', 'popular', 'hashtag', 'engagement',
            'platform', 'tiktok', 'instagram', 'twitter', 'youtube', 'reddit',
            'music', 'entertainment', 'sports', 'technology', 'fashion', 'gaming',
            'content', 'creator', 'post', 'reel', 'video', 'meme',
        ]
        question_lower = question.lower()
        keywords = [term for term in trend_terms if term in question_lower]
        # Also add non-stopwords from question
        stopwords = {'what', 'how', 'why', 'when', 'where', 'is', 'are', 'the', 'a', 'an',
                     'tell', 'me', 'about', 'show', 'can', 'you', 'give', 'your', 'its', 'of'}
        words = question_lower.split()
        keywords += [w for w in words if len(w) > 3 and w not in stopwords]
        return list(set(keywords))[:10]
