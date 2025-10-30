# home/urls.py
from django.urls import path
from . import views

app_name = "home"

urlpatterns = [
    path("", views.index, name="home"),
    path("our-story/", views.OurStoryView.as_view(), name="our_story"),
    path("careers/", views.CareersView.as_view(), name="careers"),
    path("modern-slavery-statement/", views.ModernSlaveryView.as_view(), name="modern_slavery"),
    path("privacy/", views.privacy, name="privacy"),
    path("terms/", views.terms, name="terms"),
]
