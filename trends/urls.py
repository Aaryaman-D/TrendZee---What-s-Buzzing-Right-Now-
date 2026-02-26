from django.urls import path
from . import views

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('<int:pk>/', views.TrendDetailView.as_view(), name='trend_detail'),
    path('<int:pk>/save/', views.toggle_save_trend, name='toggle_save_trend'),
    path('<int:pk>/creator-insights/', views.CreatorInsightsView.as_view(), name='creator_insights'),
    path('saved/', views.SavedTrendsView.as_view(), name='saved_trends'),
    path('<int:pk>/comment/', views.add_comment, name='add_comment'),
    path('chatbot/', views.ChatbotView.as_view(), name='chatbot'),
]
