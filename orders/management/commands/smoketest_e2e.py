# orders/management/commands/smoketest_e2e.py
from __future__ import annotations

import re
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import connection
from django.test import Client
from django.urls import reverse

from catalog.models import Product
from orders.models import Order, Payment


class Command(BaseCommand):
    help = "End-to-end smoke test: home -> catalog -> create order -> checkout -> mock pay -> verify."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("E2E smoke test starting…"))

        # -- Make sure test host is allowed -------------------------------------------------
        for host in ("testserver", "localhost", "127.0.0.1"):
            if host not in settings.ALLOWED_HOSTS:
                settings.ALLOWED_HOSTS.append(host)

        # -- Show current search_path (useful with Postgres schemas) ------------------------
        with connection.cursor() as cur:
            cur.execute("SHOW search_path;")
            sp = cur.fetchone()[0]
        self.stdout.write(f"search_path: {sp}")

        # -- Ensure a product exists --------------------------------------------------------
        p = Product.objects.first()
        if not p:
            self.stdout.write(self.style.ERROR("No products found. Load fixtures first."))
            return
        self.stdout.write(self.style.SUCCESS(f"Using product: {p.sku} / {p.name[:50]}"))

        # -- Create/login a user ------------------------------------------------------------
        User = get_user_model()
        email = "smoketest@example.com"
        user, _ = User.objects.get_or_create(
            username="smoketest",
            defaults={"email": email}
        )
        user.email = email
        user.set_password("pass1234!")
        user.save(update_fields=["email", "password"])

        client = Client()
        assert client.login(username="smoketest", password="pass1234!"), "Login failed"

        # -- Put a single item into the session cart ---------------------------------------
        s = client.session
        s["cart"] = {p.sku: 1}
        s.save()

        # -- Hit checkout_create to build the Order from the session cart -------------------
        url_create = reverse("orders:checkout_create")
        r = client.post(url_create, HTTP_HOST="testserver")
        self._expect_redirect(r, "checkout_create")

        # Extract order id from the redirect to order_detail
        order_id = self._extract_pk_from_redirect(r)
        order = Order.objects.get(pk=order_id)
        self.stdout.write(self.style.SUCCESS(f"Order created: #{order.pk} (status={order.status})"))

        # -- Fill buyer & shipping details --------------------------------------------------
        url_checkout = reverse("orders:order_checkout", kwargs={"pk": order.pk})
        payload = {
            "buyer_name": "Smoke Test",
            "buyer_email": "smoketest@example.com",
            "buyer_phone": "0123456789",
            "ship_address1": "1 Test Street",
            "ship_address2": "",
            "ship_city": "Testville",
            "ship_postcode": "TS1 2AB",
            "ship_country": "GB",
            "notes": "e2e",
            "action": "save",  # just save details first
        }
        r = client.post(url_checkout, data=payload, HTTP_HOST="testserver")
        self._expect_redirect(r, "order_checkout(save)")
        order.refresh_from_db()
        self.stdout.write(self.style.SUCCESS("Saved buyer/shipping details."))

        # -- Do a mock "successful" payment via payment_return ------------------------------
        #  payment_return view supports:
        #   ?order=<id>&status=success|failure&ref=…
        url_return = reverse("orders:payment_return")
        r = client.get(
            url_return,
            {"order": order.pk, "status": "success", "ref": "e2e-mock"},
            HTTP_HOST="testserver",
        )
        self._expect_redirect(r, "payment_return")

        # -- Verify -------------------------------------------------------------------------
        order.refresh_from_db()
        assert str(order.status).lower() == "paid", f"Order not paid; status={order.status}"
        has_payment = order.payments.filter(status=Payment.Status.SUCCESS).exists()
        assert has_payment, "No successful payment recorded."

        self.stdout.write(self.style.SUCCESS(f"E2E OK: order #{order.pk} is PAID."))

    # ----------------- helpers -------------------------------------------------------------

    def _expect_redirect(self, response, step_name: str):
        if response.status_code not in (302, 303):
            raise AssertionError(
                f"{step_name}: expected redirect, got {response.status_code}"
            )

    def _extract_pk_from_redirect(self, response) -> int:
        """
        Extract numeric pk from a redirect Location header that points to /orders/<pk>/…
        """
        loc = response.headers.get("Location") or ""
        m = re.search(r"/orders/(\d+)", loc)
        if not m:
            raise AssertionError(f"Could not find order id in redirect Location: {loc!r}")
        return int(m.group(1))
