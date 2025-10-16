from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from .services import create_order_from_cart
from .models import Order

def checkout_create(request):
    # Session cart example: {"SKU1": 2, "SKU2": 1}
    cart = request.session.get("cart", {})
    if not cart:
        messages.warning(request, "Your bag is empty.")
        return redirect("catalog:product_list")

    cart_items = [{"sku": sku, "qty": qty} for sku, qty in cart.items()]
    order = create_order_from_cart(request.user, cart_items)

    # Clear cart (or keep until payment step)
    request.session["cart"] = {}
    request.session.modified = True

    messages.success(request, f"Order #{order.pk} created (status: {order.status}).")
    return redirect("orders:order_detail", pk=order.pk)

def order_detail(request, pk):
    order = get_object_or_404(Order.objects.prefetch_related("items__product"), pk=pk)
    return render(request, "orders/order_detail.html", {"order": order})
