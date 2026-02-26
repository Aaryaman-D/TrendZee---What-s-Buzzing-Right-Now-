from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views import View
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
import json
import time

from .models import Trend, SavedTrend, Comment
from services.trend_service import TrendService
from services.gemini_service import GeminiService


class DashboardView(View):
    template_name = 'trends/dashboard.html'

    def get(self, request):
        category = request.GET.get('category', '')
        search = request.GET.get('search', '')
        platform = request.GET.get('platform', '')
        source = request.GET.get('source', '')

        trends = TrendService.get_filtered_trends(
            category=category,
            search=search,
            platform=platform,
            source=source,
        )
        top_trends = TrendService.get_top_trends(limit=10)
        categories = Trend.CATEGORY_CHOICES
        platforms = Trend.PLATFORM_CHOICES
        sources = Trend.SOURCE_CHOICES

        # Pagination
        paginator = Paginator(trends, 20)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        saved_ids = []
        if request.user.is_authenticated:
            saved_ids = list(
                SavedTrend.objects.filter(user=request.user).values_list('trend_id', flat=True)
            )

        context = {
            'trends': page_obj,
            'page_obj': page_obj,
            'top_trends': top_trends,
            'categories': categories,
            'platforms': platforms,
            'sources': sources,
            'selected_category': category,
            'selected_platform': platform,
            'selected_source': source,
            'search_query': search,
            'saved_ids': saved_ids,
        }
        return render(request, self.template_name, context)


class TrendDetailView(View):
    template_name = 'trends/trend_detail.html'

    def get(self, request, pk):
        trend = get_object_or_404(Trend, pk=pk)
        ai_explanation = GeminiService.explain_trend(trend)
        is_saved = False
        if request.user.is_authenticated:
            is_saved = SavedTrend.objects.filter(user=request.user, trend=trend).exists()

        related_trends = Trend.objects.filter(category=trend.category).exclude(pk=pk).order_by('-score')[:5]
        comments = trend.trend_comments.select_related('author').all()[:50]

        context = {
            'trend': trend,
            'ai_explanation': ai_explanation,
            'is_saved': is_saved,
            'related_trends': related_trends,
            'comments': comments,
        }
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class SavedTrendsView(View):
    template_name = 'trends/saved_trends.html'

    def get(self, request):
        saved = SavedTrend.objects.filter(user=request.user).select_related('trend')
        return render(request, self.template_name, {'saved_trends': saved})


@login_required
@require_POST
def toggle_save_trend(request, pk):
    trend = get_object_or_404(Trend, pk=pk)
    saved, created = SavedTrend.objects.get_or_create(user=request.user, trend=trend)
    if not created:
        saved.delete()
        return JsonResponse({'saved': False, 'message': 'Trend removed from saved'})
    return JsonResponse({'saved': True, 'message': 'Trend saved successfully'})


@login_required
@require_POST
def add_comment(request, pk):
    trend = get_object_or_404(Trend, pk=pk)
    text = request.POST.get('text', '').strip()
    if not text:
        return JsonResponse({'error': 'Comment cannot be empty'}, status=400)
    if len(text) > 1000:
        return JsonResponse({'error': 'Comment too long (max 1000 characters)'}, status=400)
    comment = Comment.objects.create(trend=trend, author=request.user, text=text)
    return JsonResponse({
        'success': True,
        'comment': {
            'id': comment.id,
            'author': comment.author.display_name,
            'text': comment.text,
            'created_at': comment.created_at.strftime('%b %d, %Y %H:%M'),
        }
    })


@method_decorator(login_required, name='dispatch')
class ChatbotView(View):
    template_name = 'trends/chatbot.html'
    RATE_LIMIT = 20  # max requests per minute

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        # Simple session-based rate limiting
        now = time.time()
        timestamps = request.session.get('chatbot_timestamps', [])
        timestamps = [t for t in timestamps if now - t < 60]
        if len(timestamps) >= self.RATE_LIMIT:
            return JsonResponse({
                'error': 'Rate limit exceeded. Please wait a moment before sending another message.'
            }, status=429)
        timestamps.append(now)
        request.session['chatbot_timestamps'] = timestamps

        try:
            data = json.loads(request.body)
            question = data.get('question', '').strip()
            history = data.get('history', [])
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid request'}, status=400)

        if not question:
            return JsonResponse({'error': 'Question cannot be empty'}, status=400)

        response = GeminiService.chatbot_response(question, history)
        return JsonResponse({'response': response})


@method_decorator(login_required, name='dispatch')
class CreatorInsightsView(View):
    template_name = 'trends/creator_insights.html'

    def get(self, request, pk):
        if not request.user.is_premium:
            return redirect('upgrade')
        trend = get_object_or_404(Trend, pk=pk)
        insights = GeminiService.get_creator_insights(trend)
        return render(request, self.template_name, {'trend': trend, 'insights': insights})
