# home/views.py
from django.shortcuts import render
from django.views.generic import TemplateView

def index(request):
    return render(request, "home/index.html")

class OurStoryView(TemplateView):
    template_name = "home/our_story.html"

class CareersView(TemplateView):
    template_name = "home/careers.html"

class PressView(TemplateView):
    template_name = "home/press.html"

class ModernSlaveryView(TemplateView):
    template_name = "home/modern_slavery.html"
