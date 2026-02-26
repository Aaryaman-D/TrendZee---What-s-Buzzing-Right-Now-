from django.urls import path
from . import views

urlpatterns = [
    path('', views.LandingView.as_view(), name='landing'),
    path('dashboard/', views.LandingView.as_view(), name='dashboard_home'),
    path('upgrade/', views.UpgradeView.as_view(), name='upgrade'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('privacy/', views.PrivacyView.as_view(), name='privacy'),
]
