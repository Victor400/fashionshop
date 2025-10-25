from decimal import Decimal

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_GET

from .models import Order, Payment
from .services import create_order_from_cart, record_payment
from .forms import CheckoutDetailsForm


@require_http_methods(["GET", "POST"])
def checkout_create(request):
    """
    Build an Order from the session cart and redirect to its detail page.
    (Cart is intentionally NOT cleared here so the user can still change it.)
    """
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

    messages.success(request, f"Order #{order.pk} created (status: {order.status}).")
    return redirect("orders:order_detail", pk=order.pk)


def order_detail(request, pk):
    """
    Show order summary with items and totals.
    """
    order = get_object_or_404(
        Order.objects.prefetch_related("items__product"),
        pk=pk,
    )
    return render(request, "orders/order_detail.html", {"order": order})


@require_http_methods(["GET", "POST"])
def order_checkout(request, pk):
    """
    Collect buyer/contact/shipping details for an existing pending order.
    """
    order = get_object_or_404(Order, pk=pk)

    if request.method == "POST":
        form = CheckoutDetailsForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, "Details saved. You can now pay.")
            return redirect("orders:pay_mock", pk=order.pk)  # replace with Stripe later
    else:
        form = CheckoutDetailsForm(instance=order)

    return render(request, "orders/order_checkout.html", {"order": order, "form": form})


def pay_mock(request, pk):
    """
    Very simple mock payment page with Success / Fail buttons.
    """
    order = get_object_or_404(Order, pk=pk)
    return render(request, "orders/pay_mock.html", {"order": order})


@require_GET
def payment_return(request):
    """
    /orders/return/?order=<id>&status=success|failure&ref=MOCK-123
    Creates a Payment row and marks the order paid on success.
    """
    order_id = request.GET.get("order")
    result = request.GET.get("status")
    ref = request.GET.get("ref") or None

    if not order_id:
        messages.error(request, "Missing order reference.")
        return redirect("catalog:product_list")

    order = get_object_or_404(Order, pk=order_id)

    if str(order.status).lower() == "paid":
        messages.info(request, f"Order #{order.pk} is already paid.")
        return redirect("orders:order_detail", pk=order.pk)

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
        # clear cart now that a successful payment happened
        request.session["cart"] = {}
        request.session.modified = True
    else:
        messages.error(request, "Payment failed or was cancelled. Your order is still pending.")

    return redirect("orders:order_detail", pk=order.pk)
