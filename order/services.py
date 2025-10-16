from decimal import Decimal
from django.db import transaction
from catalog.models import Product
from .models import Order, OrderItem

@transaction.atomic
def create_order_from_cart(user, cart_items):
    """
    cart_items: [{"sku": "TEE-001", "qty": 2}, ...]
    """
    order = Order.objects.create(
        user=user if getattr(user, "is_authenticated", False) else None,
        status="pending",
        total_amount=Decimal("0.00"),
    )

    running = Decimal("0.00")
    for item in cart_items:
        sku = item["sku"]
        qty = int(item["qty"])
        product = Product.objects.get(sku=sku)

        unit = Order.q2(Decimal(product.price))
        line = Order.q2(unit * qty)

        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=qty,
            price_each=unit,
        )
        running += line

    order.total_amount = Order.q2(running)
    order.save(update_fields=["total_amount"])
    return order
