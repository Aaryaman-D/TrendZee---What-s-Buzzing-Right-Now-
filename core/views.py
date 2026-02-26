from django.shortcuts import render
from django.views import View
from trends.models import Trend


class LandingView(View):
    template_name = 'core/landing.html'

    def get(self, request):
        top_trends = Trend.objects.order_by('-score')[:6]
        return render(request, self.template_name, {'top_trends': top_trends})


class UpgradeView(View):
    template_name = 'core/upgrade.html'

    def get(self, request):
        return render(request, self.template_name)


class AboutView(View):
    template_name = 'core/about.html'

    def get(self, request):
        return render(request, self.template_name)


class PrivacyView(View):
    template_name = 'core/privacy.html'

    def get(self, request):
        return render(request, self.template_name)
