# home/views.py
from django.shortcuts import render
from django.views.generic import TemplateView

def index(request):
    return render(request, "home/index.html")

class OurStoryView(TemplateView):
    template_name = "home/our_story.html"

class CareersView(TemplateView):
    template_name = "home/careers.html"

class ModernSlaveryView(TemplateView):
    template_name = "home/modern_slavery.html"

def privacy(request):
    return render(request, "home/privacy.html", {"page_title": "Privacy Policy"})

def terms(request):
    return render(request, "home/terms.html", {"page_title": "Terms of Service"})
