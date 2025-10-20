from decimal import Decimal
from django.db import transaction, connection
from django.utils import timezone
from catalog.models import Product
from .models import Order, OrderItem, AppUser

def ensure_app_user_for_django_user(dj_user) -> AppUser | None:
    if not getattr(dj_user, "is_authenticated", False):
        return None
    email = (dj_user.email or "").strip()
    if not email:
        return None
    full_name = (getattr(dj_user, "get_full_name", lambda: "")() or dj_user.get_username()).strip()

    # Upsert into fashionshop.app_user by email and return id
    with connection.cursor() as cur:
        cur.execute(
            '''
            INSERT INTO "fashionshop"."app_user"(email, full_name, created_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (email) DO UPDATE SET full_name = EXCLUDED.full_name
            RETURNING id;
            ''',
            [email, full_name]
        )
        app_user_id = cur.fetchone()[0]
    return AppUser(id=app_user_id)

@transaction.atomic
def create_order_from_cart(dj_user, cart_items):
    app_user = ensure_app_user_for_django_user(dj_user)

    order = Order.objects.create(
        user=app_user,                 # FK now valid (or null)
        status="pending",
        total_amount=Decimal("0.00"),
        created_at=timezone.now(),
    )

    running = Decimal("0.00")
    for item in cart_items:
        sku = item["sku"]; qty = int(item["qty"])
        product = Product.objects.get(sku=sku)

        unit = Order.q2(Decimal(product.price))
        line = Order.q2(unit * qty)

        OrderItem.objects.create(
            order=order, product=product,
            quantity=qty, price_each=unit,
        )
        running += line

    order.total_amount = Order.q2(running)
    order.save(update_fields=["total_amount"])
    return order
