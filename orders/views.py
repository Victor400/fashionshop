from decimal import Decimal
from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from .services import create_order_from_cart
from .models import Order

@require_http_methods(["GET","POST"])
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
    order = get_object_or_404(Order.objects.prefetch_related("items__product"), pk=pk)
    return render(request, "orders/order_detail.html", {"order": order})
