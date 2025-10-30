# home/urls.py
from django.urls import path
from . import views

app_name = "home"

urlpatterns = [
    path("", views.index, name="home"),
    path("our-story/", views.OurStoryView.as_view(), name="our_story"),
    path("careers/", views.CareersView.as_view(), name="careers"),
    path("press/", views.PressView.as_view(), name="press"),
    path("modern-slavery-statement/", views.ModernSlaveryView.as_view(), name="modern_slavery"),
]
