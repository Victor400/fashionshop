from decimal import Decimal

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_GET

from .models import Order
from .services import (
    create_order_from_cart,
    record_payment,
    PAYMENT_METHOD_CARD,
    PAYMENT_STATUS_SUCCESS,
    PAYMENT_STATUS_FAILED,
)


@require_http_methods(["GET", "POST"])
def checkout_create(request):
    cart = request.session.get("cart", {}) or {}
    normalized = []
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

    # Clear bag AFTER order creation
    request.session["cart"] = {}
    request.session.modified = True

    messages.success(request, f"Order #{order.pk} created (status: {order.status}).")
    return redirect("orders:order_detail", pk=order.pk)


def order_detail(request, pk):
    order = get_object_or_404(
        Order.objects.prefetch_related("items__product"),
        pk=pk,
    )
    return render(request, "orders/order_detail.html", {"order": order})


def pay_mock(request, pk):
    """Very simple mock payment page with Success / Fail buttons."""
    order = get_object_or_404(Order, pk=pk)
    return render(request, "orders/pay_mock.html", {"order": order})


@require_GET
def payment_return(request):
    """
    /orders/return/?order=<id>&status=success|failure&ref=MOCK-123
    """
    order_id = request.GET.get("order")
    result = request.GET.get("status")
    ref = request.GET.get("ref") or None

    if not order_id:
        messages.error(request, "Missing order reference.")
        return redirect("catalog:product_list")

    order = get_object_or_404(Order, pk=order_id)

    # Prevent double capture UX
    if str(order.status).lower() == "paid":
        messages.info(request, f"Order #{order.pk} is already paid.")
        return redirect("orders:order_detail", pk=order.pk)

    status = PAYMENT_STATUS_SUCCESS if result == "success" else PAYMENT_STATUS_FAILED

    payment = record_payment(
        order=order,
        provider="mock",
        method=PAYMENT_METHOD_CARD,
        status=status,
        amount=Decimal(order.total_amount),
        provider_ref=ref,
    )

    if payment.status == PAYMENT_STATUS_SUCCESS:
        messages.success(request, f"Payment successful. Order #{order.pk} is now paid.")
        request.session["cart"] = {}
        request.session.modified = True
    else:
        messages.error(request, "Payment failed or was cancelled. Your order is still pending.")

    return redirect("orders:order_detail", pk=order.pk)
