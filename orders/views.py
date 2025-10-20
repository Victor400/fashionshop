# orders/views.py
from decimal import Decimal
from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .services import create_order_from_cart
from .models import Order


@require_http_methods(["GET", "POST"])
def checkout_create(request):
    """
    Build an Order from the session cart and redirect to its detail page.
    Session cart format: {"SKU1": 2, "SKU2": 1}
    """
    cart = request.session.get("cart", {}) or {}

    # Normalize/validate quantities to integers >= 1
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
        # Don’t clear the cart on failure
        messages.error(request, f"Sorry, we couldn't create your order: {exc}")
        return redirect("catalog:product_list")

    # Clear cart after we’ve created the order
    request.session["cart"] = {}
    request.session.modified = True

    messages.success(request, f"Order #{order.pk} created (status: {order.status}).")
    return redirect("orders:order_detail", pk=order.pk)


def order_detail(request, pk: int):
    """
    Simple order confirmation/summary page.
    Assumes Order.items is related_name for OrderItem.
    """
    order = get_object_or_404(
        Order.objects.select_related("user").prefetch_related("items__product"),
        pk=pk,
    )
    # Optional derived values (totals checked server side already)
    line_items = [
        {
            "name": getattr(i.product, "name", f"#{i.product_id}"),
            "sku": getattr(i.product, "sku", None),
            "qty": i.quantity,
            "unit": i.price_each,
            "line": i.line_total,
        }
        for i in order.items.all()
    ]

    ctx = {
        "order": order,
        "line_items": line_items,
        "lines_total": sum((li["line"] for li in line_items), Decimal("0.00")),
    }
    return render(request, "orders/order_detail.html", ctx)
