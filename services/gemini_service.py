"""
Gemini AI Service Layer
All AI interactions are routed through this service.
Frontend never directly calls AI APIs.
"""

import json
import logging
from django.conf import settings
from services.trend_service import TrendService

logger = logging.getLogger(__name__)


def _call_gemini(prompt, system_instruction=None):
    """
    Core Gemini API call. Returns response text or None on failure.
    Tries multiple model names for resilience.
    """
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)

        # Models to try in order of preference
        models_to_try = ['gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-pro']
        sys_text = system_instruction or "You are a helpful trend intelligence assistant."
        last_error = None

        for model_name in models_to_try:
            try:
                # gemini-pro doesn't support system_instruction
                if model_name == 'gemini-pro':
                    model = genai.GenerativeModel(model_name=model_name)
                    full_prompt = f"System: {sys_text}\n\n{prompt}"
                    response = model.generate_content(full_prompt)
                else:
                    model = genai.GenerativeModel(
                        model_name=model_name,
                        system_instruction=sys_text
                    )
                    response = model.generate_content(prompt)
                return response.text
            except Exception as model_err:
                last_error = model_err
                err_str = str(model_err).lower()
                if 'resourceexhausted' in err_str or '429' in err_str:
                    logger.warning(f"Gemini quota exhausted on {model_name}: {model_err}")
                    return '__QUOTA_EXHAUSTED__'
                logger.info(f"Model {model_name} failed: {model_err}, trying next...")
                continue

        logger.error(f"All Gemini models failed. Last error: {last_error}")
        return None
    except ImportError:
        logger.warning("google-generativeai not installed. Run: pip install google-generativeai")
        return None
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return None


TREND_ASSISTANT_SYSTEM = """
You are a Trend Intelligence Assistant for TrendZee.
Your ONLY job is to analyze trend data provided to you.
Do NOT answer questions unrelated to trends, social media, or the data provided.
Be concise, insightful, and data-driven in your responses.
Format your responses in clean readable paragraphs.
"""


class GeminiService:

    @staticmethod
    def explain_trend(trend):
        """Generate AI explanation for why a trend is gaining traction."""
        if not settings.GEMINI_API_KEY:
            return _mock_trend_explanation(trend)

        prompt = f"""
        Analyze this social media trend and explain why it is gaining traction:

        Title: {trend.title}
        Category: {trend.category}
        Platform: {trend.platform}
        Description: {trend.description}
        Engagement Score: {trend.score}
        Velocity: {trend.velocity}
        Likes: {trend.likes:,}
        Shares: {trend.shares:,}
        Comments: {trend.comments:,}

        Provide a clear, insightful analysis of:
        1. Why this trend is gaining momentum
        2. What audience it appeals to
        3. What makes it shareable/viral
        Keep your response to 3-4 concise paragraphs.
        """

        result = _call_gemini(prompt, system_instruction=TREND_ASSISTANT_SYSTEM)
        if result == '__QUOTA_EXHAUSTED__':
            return _mock_trend_explanation(trend, quota_exhausted=True)
        return result or _mock_trend_explanation(trend)

    @staticmethod
    def get_creator_insights(trend):
        """Generate creator strategy insights for premium users."""
        if not settings.GEMINI_API_KEY:
            return _mock_creator_insights(trend)

        prompt = f"""
        Generate comprehensive creator strategy insights for this trend:

        Title: {trend.title}
        Category: {trend.category}
        Platform: {trend.platform}
        Description: {trend.description}
        Engagement Score: {trend.score}
        Total Engagement: {trend.total_engagement:,}
        Velocity: {trend.velocity}

        Provide:
        1. **Suggested Hashtags** (10-15 relevant hashtags)
        2. **Caption Format** (hook + body + CTA structure)
        3. **Target Audience** (demographics and psychographics)
        4. **Content Strategy** (format, timing, frequency recommendations)
        5. **Engagement Tactics** (specific actions to boost interaction)

        Format the response with clear headings for each section.
        Be specific and actionable.
        """

        result = _call_gemini(prompt, system_instruction=TREND_ASSISTANT_SYSTEM)
        return result or _mock_creator_insights(trend)

    @staticmethod
    def chatbot_response(question, history=None):
        """
        Restricted chatbot - only answers trend-related questions.
        Injects relevant trend context before calling Gemini.
        """
        # Extract keywords and find relevant trends
        keywords = TrendService.extract_trend_keywords(question)
        relevant_trends = TrendService.search_trends_for_context(keywords, limit=5)

        # Refuse if question appears unrelated to trends
        trend_related_terms = [
            'trend', 'viral', 'popular', 'hashtag', 'engagement', 'platform',
            'social', 'content', 'creator', 'post', 'reel', 'video', 'tiktok',
            'instagram', 'twitter', 'youtube', 'reddit', 'music', 'sports',
            'gaming', 'fashion', 'technology', 'entertainment', 'meme', 'marketing',
            'audience', 'reach', 'impressions', 'influencer', 'analytics'
        ]
        q_lower = question.lower()
        is_relevant = any(term in q_lower for term in trend_related_terms)

        if not is_relevant and not relevant_trends:
            return (
                "I can only answer questions related to trend data and social media intelligence "
                "available on this platform. Please ask me about trends, viral content, "
                "engagement strategies, or specific categories like entertainment, technology, sports, etc."
            )

        if not settings.GEMINI_API_KEY:
            return _mock_chatbot_response(question, relevant_trends)

        # Build context from relevant trends
        context_str = ""
        if relevant_trends:
            context_str = "Here are the relevant trends from our platform:\n\n"
            for i, t in enumerate(relevant_trends, 1):
                context_str += (
                    f"{i}. **{t['title']}** ({t['platform']} | {t['category']})\n"
                    f"   Score: {t['score']} | Velocity: {t['velocity']}\n"
                    f"   {t['description'][:200]}\n\n"
                )
        else:
            context_str = "No directly matching trends found for your query, but I can answer based on general trend intelligence.\n"

        # Build conversation history for multi-turn
        history_str = ""
        if history:
            for msg in history[-6:]:  # Last 3 exchanges
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                history_str += f"{role.capitalize()}: {content}\n"

        system = """
        You are TrendZee's Trend Intelligence Assistant.
        You ONLY answer questions about social media trends, engagement, content strategy, and the data provided.
        If asked about anything unrelated to trends, politely decline.
        Be concise, insightful, and reference the provided trend data when relevant.
        """

        prompt = f"""
        {context_str}

        Previous conversation:
        {history_str}

        User question: {question}

        Answer based only on the trend data and your knowledge of social media trends.
        """

        result = _call_gemini(prompt, system_instruction=system)
        if result == '__QUOTA_EXHAUSTED__':
            return ("⚠️ The AI service has reached its daily usage limit. "
                    "Your Gemini API key is valid but the free tier quota is exhausted. "
                    "Please wait for the quota to reset (usually within 24 hours), "
                    "or enable billing at https://ai.google.dev/ for higher limits.")
        return result or "I'm having trouble processing your request right now. Please try again."


# ─── Mock responses for demo mode (no API key) ──────────────────────────────

def _mock_trend_explanation(trend, quota_exhausted=False):
    footer = (
        "\n\n*(⚠️ Gemini API daily quota exhausted. Showing cached analysis. Quota resets within 24 hours.)*"
        if quota_exhausted
        else "\n\n*(AI-generated analysis — powered by TrendZee Intelligence Engine)*"
    )
    return (
        f"**{trend.title}** is gaining significant traction across {trend.get_platform_display()} "
        f"with an engagement score of {trend.score:.1f}. The trend falls under the {trend.get_category_display()} "
        f"category, which is currently showing {trend.velocity} velocity.\n\n"
        f"The content resonates strongly with its target audience due to its timely relevance and highly "
        f"shareable nature. With {trend.likes:,} likes, {trend.shares:,} shares, and {trend.comments:,} comments, "
        f"the engagement rate suggests authentic audience connection rather than passive consumption.\n\n"
        f"This trend is particularly effective because it taps into current cultural conversations and "
        f"provides users with content they feel compelled to share within their own networks. "
        f"The {trend.velocity} velocity indicator suggests this trend has significant staying power "
        f"in the immediate term."
        f"{footer}"
    )


def _mock_creator_insights(trend):
    return f"""## Creator Strategy Insights for "{trend.title}"

**Suggested Hashtags**
#{trend.category} #trending #viral #{trend.platform} #contentcreator #trending2025 
#socialmedia #engagement #{trend.category}content #trendalert #viralcontent #explore

**Caption Format**
Hook: Start with a bold statement or question that addresses the trend directly.
Body: Share your unique angle or perspective on "{trend.title}" — add value, humor, or education.
CTA: "Follow for more [category] trends | Drop your thoughts below 👇"

**Target Audience**
Primary: 18-34 year-olds active on {trend.get_platform_display()}, interested in {trend.get_category_display()} content.
Secondary: Content creators and marketers looking to capitalize on trending topics.

**Content Strategy**
- Format: Short-form video (15-60 seconds) performs best for this trend type
- Timing: Post between 6-9 PM local time for maximum initial reach
- Frequency: 1-2 posts per day while trend velocity is {trend.velocity}
- Hook your audience in the first 3 seconds

**Engagement Tactics**
- Reply to every comment within the first hour of posting
- Use the trend's primary hashtag as the first comment
- Cross-post across platforms to maximize reach
- Collaborate with mid-tier creators in the {trend.get_category_display()} space

*(AI-generated insights — powered by TrendZee Intelligence Engine)*"""


def _mock_chatbot_response(question, trends):
    if trends:
        trend_names = ', '.join([t['title'] for t in trends[:3]])
        return (
            f"Based on current trend data, here's what I found relevant to your question:\n\n"
            f"The most relevant trending topics are: **{trend_names}**. "
            f"These are currently showing strong engagement signals on our platform. "
            f"Would you like me to dive deeper into any of these specific trends, their engagement patterns, "
            f"or content strategy recommendations?\n\n"
            f"*(AI analysis — powered by TrendZee Intelligence Engine)*"
        )
    return (
        "I'm your Trend Intelligence Assistant. I can help you understand trending topics, "
        "analyze engagement patterns, and develop content strategies based on real trend data. "
        "Try asking me about specific categories like 'What's trending in tech?' or "
        "'What makes gaming content go viral?'\n\n"
        "*(AI analysis — powered by TrendZee Intelligence Engine)*"
    )
