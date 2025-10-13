# fashionshop/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("", include(("home.urls", "home"), namespace="home")),     # ← namespaced
    path("shop/", include(("catalog.urls", "catalog"), namespace="catalog")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

