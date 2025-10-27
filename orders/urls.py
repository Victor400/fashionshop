# orders/urls.py
from django.urls import path
from . import views
from .webhooks import stripe_webhook

app_name = "orders"

urlpatterns = [
    path("checkout/", views.checkout_create, name="checkout_create"),
    path("<int:pk>/", views.order_detail, name="order_detail"),
    path("<int:pk>/checkout/", views.order_checkout, name="order_checkout"),
    path("<int:pk>/pay/", views.pay_mock, name="pay_mock"),
    path("<int:pk>/pay/stripe/", views.pay_stripe, name="pay_stripe"),
    path("return/", views.payment_return, name="payment_return"),
    path("stripe/webhook/", stripe_webhook, name="stripe_webhook"),
    path("<int:pk>/status/", views.order_status_update, name="order_status_update"),
]

