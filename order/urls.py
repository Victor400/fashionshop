# orders/urls.py
from django.urls import path
from . import views

app_name = "orders"
urlpatterns = [
    path("checkout/", views.checkout_create, name="checkout_create"),
    path("<int:pk>/", views.order_detail, name="order_detail"),
]
