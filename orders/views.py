# orders/views.py
from __future__ import annotations

from decimal import Decimal

import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_GET, require_POST

from .forms import CheckoutDetailsForm, OrderStatusForm
from .models import Order, Payment
from .services import (
    create_order_from_cart,
    record_payment,
    set_order_status,
)

# Configure Stripe (safe if missing in local dev)
stripe.api_key = getattr(settings, "STRIPE_SECRET_KEY", "") or None


# -----------------------------
# Create order from session cart
# -----------------------------
@require_http_methods(["GET", "POST"])
def checkout_create(request):
    """
    Build an Order from the session cart and redirect to its detail page.
    (Cart is NOT cleared here so the user can still edit it.)
    """
    cart = request.session.get("cart", {}) or {}
    normalized: list[dict[str, int | str]] = []
    for sku, qty in cart.items():
        try:
            n = int(qty)
        except (TypeError, ValueError):
            n = 0
        if n > 0:
            normalized.append({"sku": sku, "qty": n})

    if not normalized:
        messages.warning(request, "Your bag is empty.")
        return redirect("catalog:product_list")

    try:
        order = create_order_from_cart(request.user, normalized)
    except Exception as exc:
        messages.error(request, f"Sorry, we couldn't create your order: {exc}")
        return redirect("catalog:product_list")

    messages.success(request, f"Order #{order.pk} created (status: {order.status}).")
    return redirect("orders:order_detail", pk=order.pk)


# -----------------------------
# Order detail
# -----------------------------
def order_detail(request, pk):
    """Show order summary with items, totals, buyer/shipping and payments."""
    order = get_object_or_404(
        Order.objects.prefetch_related("items__product", "payments"),
        pk=pk,
    )
    return render(request, "orders/order_detail.html", {"order": order})


# -----------------------------
# Collect buyer/shipping details
# -----------------------------
@require_http_methods(["GET", "POST"])
def order_checkout(request, pk):
    """
    Collect buyer/contact/shipping details for an existing order.

    - POST with action=save -> save, go back to order detail
    - POST with action=pay  -> save, then redirect to Stripe checkout
    """
    order = get_object_or_404(Order, pk=pk)
    if request.method == "POST":
        form = CheckoutDetailsForm(request.POST, instance=order)
        if form.is_valid():
            form.save()  # writes buyer_*/ship_* into fashionshop.order
            if request.POST.get("action") == "pay":
                return redirect("orders:pay_stripe", pk=order.pk)
            messages.success(request, "Details saved.")
            return redirect("orders:order_detail", pk=order.pk)
    else:
        form = CheckoutDetailsForm(instance=order)
    return render(request, "orders/order_checkout.html", {"order": order, "form": form})


# -----------------------------
# Mock payment page (optional)
# -----------------------------
def pay_mock(request, pk):
    """Very simple mock payment page with Success / Fail buttons."""
    order = get_object_or_404(Order, pk=pk)
    return render(request, "orders/pay_mock.html", {"order": order})


# -----------------------------
# Stripe: create Checkout Session
# -----------------------------
@require_http_methods(["GET", "POST"])
def pay_stripe(request, pk):
    """
    Creates a Stripe Checkout Session for the order and redirects to Stripe.
    No webhooks: we verify on return using session_id.
    """
    order = get_object_or_404(Order.objects.prefetch_related("items__product"), pk=pk)

    if str(order.status).lower() == "paid":
        messages.info(request, f"Order #{order.pk} is already paid.")
        return redirect("orders:order_detail", pk=order.pk)

    if not stripe.api_key:
        messages.error(request, "Stripe is not configured.")
        return redirect("orders:order_detail", pk=order.pk)

    # Build line items (amounts in the smallest currency unit – pence)
    line_items: list[dict] = []
    currency = getattr(settings, "STRIPE_CURRENCY", "gbp")
    for it in order.items.all():
        name = it.product.name if it.product else f"SKU {it.product_id}"
        unit_amount = int(Decimal(it.price_each) * 100)
        line_items.append(
            {
                "price_data": {
                    "currency": currency,
                    "product_data": {"name": name},
                    "unit_amount": unit_amount,
                },
                "quantity": it.quantity,
            }
        )

    success_url = (
        request.build_absolute_uri(reverse("orders:payment_return"))
        + f"?order={order.pk}&provider=stripe&session_id={{CHECKOUT_SESSION_ID}}"
    )
    cancel_url = request.build_absolute_uri(
        reverse("orders:order_detail", kwargs={"pk": order.pk})
    )

    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=line_items,
            success_url=success_url,
            cancel_url=cancel_url,
        )
    except Exception as exc:
        messages.error(request, f"Could not start payment: {exc}")
        return redirect("orders:order_detail", pk=order.pk)

    return redirect(session.url, permanent=False)


# -----------------------------
# Payment return (Stripe & Mock)
# -----------------------------
@require_GET
def payment_return(request):
    """
    Handles both mock and Stripe returns.

    - Stripe: ?order=<id>&provider=stripe&session_id=cs_test_...
    - Mock:   ?order=<id>&status=success|failure&ref=...
    """
    order_id = request.GET.get("order")
    if not order_id:
        messages.error(request, "Missing order reference.")
        return redirect("catalog:product_list")

    order = get_object_or_404(Order, pk=order_id)

    # Already paid? Bail early.
    if str(order.status).lower() == "paid":
        messages.info(request, f"Order #{order.pk} is already paid.")
        return redirect("orders:order_detail", pk=order.pk)

    provider = (request.GET.get("provider") or "").lower()

    if provider == "stripe":
        session_id = request.GET.get("session_id")
        if not session_id:
            messages.error(request, "Missing payment session.")
            return redirect("orders:order_detail", pk=order.pk)

        try:
            session = stripe.checkout.Session.retrieve(
                session_id,
                expand=["payment_intent"],
            )
        except Exception as exc:
            messages.error(request, f"Could not verify payment: {exc}")
            return redirect("orders:order_detail", pk=order.pk)

        if session.payment_status == "paid" or (
            session.payment_intent and session.payment_intent.status == "succeeded"
        ):
            record_payment(
                order=order,
                provider="stripe",
                method=Payment.Method.CARD,
                status=Payment.Status.SUCCESS,
                amount=Decimal(order.total_amount),
                provider_ref=session.payment_intent.id if session.payment_intent else session.id,
            )
            messages.success(request, f"Payment successful. Order #{order.pk} is now paid.")
            request.session["cart"] = {}
            request.session.modified = True
        else:
            record_payment(
                order=order,
                provider="stripe",
                method=Payment.Method.CARD,
                status=Payment.Status.FAILED,
                amount=Decimal(order.total_amount),
                provider_ref=session.id,
            )
            messages.error(request, "Payment not completed.")
        return redirect("orders:order_detail", pk=order.pk)

    # Fallback: mock flow
    result = request.GET.get("status")
    ref = request.GET.get("ref") or None
    status = Payment.Status.SUCCESS if result == "success" else Payment.Status.FAILED

    payment = record_payment(
        order=order,
        provider="mock",
        method=Payment.Method.CARD,
        status=status,
        amount=Decimal(order.total_amount),
        provider_ref=ref,
    )

    if payment.status == Payment.Status.SUCCESS:
        messages.success(request, f"Payment successful. Order #{order.pk} is now paid.")
        request.session["cart"] = {}
        request.session.modified = True
    else:
        messages.error(request, "Payment failed or was cancelled.")
    return redirect("orders:order_detail", pk=order.pk)


# -----------------------------
# Staff: update order status
# -----------------------------
def _staff(user):  # simple helper for the decorator
    return user.is_authenticated and user.is_staff


@user_passes_test(_staff, login_url="account_login")
def order_status_update(request, pk):
    order = get_object_or_404(Order, pk=pk)
    form = OrderStatusForm(request.POST or None, order=order)

    if request.method == "POST":
        if form.is_valid():
            try:
                set_order_status(order, form.cleaned_data["to_status"], by_user=request.user)
                messages.success(
                    request,
                    f"Order #{order.pk} status updated to “{form.cleaned_data['to_status']}”.",
                )
                return redirect("orders:order_detail", pk=order.pk)
            except ValueError as e:
                messages.error(request, str(e))

    return render(request, "orders/order_status_form.html", {"order": order, "form": form})
