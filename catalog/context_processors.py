from decimal import Decimal
from catalog.models import Product

def bag_summary(request):
    cart = request.session.get("cart", {})
    if not cart:
        return {"bag_items_count": 0, "grand_total": Decimal("0.00")}

    products = {p.sku: p for p in Product.objects.filter(sku__in=cart.keys())}
    items = 0
    total = Decimal("0.00")
    for sku, qty in cart.items():
        p = products.get(sku)
        if not p:
            continue
        q = int(qty)
        items += q
        total += Decimal(p.price) * q

    return {
        "bag_items_count": items,
        "grand_total": total.quantize(Decimal("0.01")),
    }
