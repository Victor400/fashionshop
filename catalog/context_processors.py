# catalog/context_processors.py
from decimal import Decimal
from catalog.models import Product

def bag_summary(request):
    """
    Inject session cart totals into templates:
    - bag_items_count
    - grand_total (Decimal)
    """
    cart = request.session.get("cart", {})
    items = 0
    total = Decimal("0.00")

    if cart:
        # fetch prices only for SKUs in the cart
        products = {p.sku: p for p in Product.objects.filter(sku__in=cart.keys())}
        for sku, qty in cart.items():
            try:
                p = products[sku]
                items += int(qty)
                total += Decimal(p.price) * int(qty)
            except KeyError:
                # SKU not found -> ignore stale entry
                pass

    return {
        "bag_items_count": items,
        "grand_total": total.quantize(Decimal("0.01")),
    }
