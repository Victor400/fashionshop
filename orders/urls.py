# orders/urls.py
from django.urls import path
from .views import checkout_create, order_detail, pay_mock, payment_return

app_name = "orders"

urlpatterns = [
    path("checkout/", checkout_create, name="checkout_create"),
    path("<int:pk>/pay/", pay_mock, name="pay_mock"),
    path("return/", payment_return, name="payment_return"),
    path("<int:pk>/", order_detail, name="order_detail"),
]
