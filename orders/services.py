# orders/services.py
from __future__ import annotations
"""
Service layer for Orders:
- Ensures a mapping from Django users to fashionshop.app_user (unmanaged)
- Builds Order + OrderItem rows from a session/cart payload
- Records payments and advances order status on success
"""

from decimal import Decimal
from typing import Optional, Iterable, Mapping

from django.db import transaction, connection
from django.utils import timezone

from catalog.models import Product
from .models import Order, OrderItem, AppUser, Payment
from django.utils import timezone
from .models import Order, OrderStatusHistory

def ensure_app_user_for_django_user(dj_user) -> Optional[AppUser]:
    """
    Upsert a row in fashionshop.app_user for the given Django user (by email)
    and return a lightweight AppUser carrying the id. Returns None if the
    request user is anonymous or has no email.
    """
    if not getattr(dj_user, "is_authenticated", False):
        return None

    email = (getattr(dj_user, "email", "") or "").strip()
    if not email:
        return None

    full_name = ""
    if hasattr(dj_user, "get_full_name"):
        full_name = dj_user.get_full_name() or ""
    if not full_name:
        full_name = getattr(dj_user, "get_username", lambda: "")() or ""
    full_name = full_name.strip()

    with connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO "fashionshop"."app_user"(email, full_name, created_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (email) DO UPDATE
                SET full_name = EXCLUDED.full_name
            RETURNING id;
            """,
            [email, full_name],
        )
        app_user_id = cur.fetchone()[0]

    return AppUser(id=app_user_id)


@transaction.atomic
def create_order_from_cart(
    dj_user,
    cart_items: Iterable[Mapping[str, object]],
) -> Order:
    """
    Create an Order (status='pending') and associated OrderItem rows
    from a structure like [{'sku': 'ABC123', 'qty': 2}, ...].
    Quantizes money to 2dp and runs in a single transaction.
    """
    app_user = ensure_app_user_for_django_user(dj_user)

    order = Order.objects.create(
        user=app_user,
        status="pending",
        total_amount=Decimal("0.00"),
        created_at=timezone.now(),
    )

    running = Decimal("0.00")
    for item in cart_items:
        sku = str(item["sku"]).strip()
        qty = int(item.get("qty", 0) or 0)
        if qty <= 0:
            continue

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


def record_payment(
    order: Order,
    *,
    provider: str,
    method: str,
    status: str,
    amount: Decimal,
    provider_ref: Optional[str] = None,
    raw_payload: Optional[dict] = None,
) -> Payment:
    """
    Persist a payment and, if successful, set order.status='paid'.
    `method` and `status` must be valid Payment enum values.
    """
    if method not in Payment.Method.values:
        raise ValueError(f"Invalid payment method: {method!r}. Allowed: {list(Payment.Method.values)}")
    if status not in Payment.Status.values:
        raise ValueError(f"Invalid payment status: {status!r}. Allowed: {list(Payment.Status.values)}")

    payment = Payment.objects.create(
        order=order,
        provider=provider,
        method=method,
        status=status,
        amount=Order.q2(Decimal(amount)),
        provider_ref=provider_ref,
    )

    if status == Payment.Status.SUCCESS:
        order.status = "paid"
        order.save(update_fields=["status"])

    return payment



# Allowed linear flow + cancellation rule
ALLOWED_TRANSITIONS = {
    "pending":   {"paid", "cancelled"},
    "paid":      {"shipped"},
    "shipped":   {"delivered"},
    "delivered": set(),        # terminal
    "cancelled": set(),        # terminal
}

# Optional: normalize (lowercase)
CANON = {"pending", "paid", "shipped", "delivered", "cancelled"}

def allowed_next_statuses(current: str) -> list[str]:
    cur = (current or "").lower()
    return sorted(ALLOWED_TRANSITIONS.get(cur, set()))

def set_order_status(order: Order, to_status: str, by_user=None) -> OrderStatusHistory:
    """
    Validate and perform a status transition; record a history row with timestamp.
    Does NOT change stock (per AC).
    """
    frm = (order.status or "").lower()
    to  = (to_status or "").lower()
    if to not in CANON:
        raise ValueError(f"Unknown status: {to}")
    allowed = ALLOWED_TRANSITIONS.get(frm, set())
    if to not in allowed:
        raise ValueError(f"Transition {frm} → {to} not allowed")

    # Persist on Order
    order.status = to
    order.save(update_fields=["status"])

    # Write history row (timestamp = created_at)
    hist = OrderStatusHistory.objects.create(
        order=order, from_status=frm, to_status=to, changed_by=by_user
    )
    return hist
