# tests/test_e2e.py
from __future__ import annotations

import pytest
from decimal import Decimal

from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import Client

from catalog.models import Product
from orders.models import Order, OrderItem, Payment, OrderStatusHistory
from orders.utils import get_or_create_app_user

pytestmark = pytest.mark.django_db(transaction=True)

def _skip_if_prereqs_missing():
    # Catalog tables (managed=False) must exist with at least 1 product.
    if not Product.objects.exists():
        pytest.skip("No Product rows available. Load fixtures first (brands/categories/products).")

def test_home_and_list_pages_load(client: Client):
    # Sanity pages
    r = client.get("/")
    assert r.status_code in (200, 302)
    r = client.get(reverse("catalog:product_list"))
    assert r.status_code == 200

def test_checkout_happy_path(client: Client):
    """
    Full flow:
    - seed cart in session (1 x existing product)
    - POST /orders/checkout/create -> creates order
    - Fill buyer/ship form -> save
    - Mock-pay -> return -> paid + history row
    """
    _skip_if_prereqs_missing()

    # Create & login user (email required for app_user)
    User = get_user_model()
    u = User.objects.create_user(
        username="e2e_user",
        email="e2e@example.com",
        password="secret1234",
    )
    assert client.login(username="e2e_user", password="secret1234")

    # Seed cart in session
    p = Product.objects.first()
    with client.session as s:
        s["cart"] = {str(p.sku): 1}

    # Create order from cart
    url_create = reverse("orders:checkout_create")
    r = client.post(url_create)
    assert r.status_code in (302, 303)
    # Follow to detail
    order_detail_url = r.headers.get("Location") or r.url
    assert "/orders/" in order_detail_url
    order_id = order_detail_url.rstrip("/").split("/")[-1]
    order = Order.objects.get(pk=order_id)
    assert order.status == "pending"
    assert order.items.count() == 1
    assert order.total_amount and Decimal(order.total_amount) > 0

    # Fill buyer/ship details
    url_checkout = reverse("orders:order_checkout", kwargs={"pk": order.pk})
    payload = {
        "buyer_name": "John Tester",
        "buyer_email": "buyer@example.com",
        "buyer_phone": "0123456789",
        "ship_address1": "1 Test Way",
        "ship_address2": "",
        "ship_city": "Testville",
        "ship_postcode": "T35 7AB",
        "ship_country": "GB",
        "notes": "E2E note",
        "action": "pay",  # goes to payment route
    }
    r = client.post(url_checkout, payload)
    # pay_mock is enabled in your routes; Stripe path is separate.
    # We expect redirect either to pay_mock page or to payment_return.
    assert r.status_code in (302, 303)
    pay_url = r.headers.get("Location") or r.url
    assert pay_url

    # Use the mock payment: directly hit the payment_return with success
    payment_return = reverse("orders:payment_return")
    ret = client.get(payment_return, {
        "order": order.pk,
        "provider": "mock",
        "status": "success",
        "ref": "E2E-OK",
    })
    assert ret.status_code in (302, 303)

    order.refresh_from_db()
    assert order.status == "paid"
    assert Payment.objects.filter(order=order, status=Payment.Status.SUCCESS).exists()
    assert OrderStatusHistory.objects.filter(order=order, to_status="paid").exists()

def test_app_user_mapping_created_on_login(client: Client):
    """
    Ensures we create fashionshop.app_user row via utils.
    """
    User = get_user_model()
    u = User.objects.create_user(
        username="e2e2",
        email="e2e2@example.com",
        password="secret1234",
    )
    assert client.login(username="e2e2", password="secret1234")
    # This should upsert in fashionshop.app_user
    au = get_or_create_app_user(u)
    assert au and au.id is not None
