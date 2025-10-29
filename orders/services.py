# orders/services.py
from __future__ import annotations

from decimal import Decimal
from typing import Iterable, Mapping, Optional

from django.db import transaction, connection
from django.utils import timezone

from catalog.models import Product
from .models import AppUser, Order, OrderItem, Payment, OrderStatusHistory

# ----- AppUser helpers -------------------------------------------------

def ensure_app_user_for_django_user(dj_user) -> Optional[AppUser]:
    """
    Upsert a row in fashionshop.app_user for the given Django user (by email)
    and return an AppUser(id=...). Returns None if user is not authenticated or has no email.
    """
    if not getattr(dj_user, "is_authenticated", False):
        return None

    email = (getattr(dj_user, "email", "") or "").strip()
    if not email:
        return None

    full_name = ""
    if hasattr(dj_user, "get_full_name"):
        full_name = dj_user.get_full_name() or ""
    if not full_name and hasattr(dj_user, "get_username"):
        full_name = dj_user.get_username() or ""
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


def get_guest_app_user() -> AppUser:
    """
    Ensure a single reusable 'Guest' app_user exists for anonymous orders.
    Uses a stable email so ON CONFLICT can re-use it.
    """
    guest_email = "guest@fashionshop.local"
    with connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO "fashionshop"."app_user"(email, full_name, created_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (email) DO NOTHING;
            """,
            [guest_email, "Guest"],
        )
        # Fetch its id (exists now for sure).
        cur.execute(
            'SELECT id FROM "fashionshop"."app_user" WHERE email = %s LIMIT 1;',
            [guest_email],
        )
        row = cur.fetchone()
        if not row:
            raise RuntimeError("Could not create or find guest AppUser.")
        return AppUser(id=row[0])


def _resolve_app_user(dj_user) -> AppUser:
    """
    Resolve to an AppUser row:
    - logged-in user → upsert by email (ensure_app_user_for_django_user)
    - anonymous → reusable guest AppUser
    """
    app_user = ensure_app_user_for_django_user(dj_user)
    return app_user or get_guest_app_user()

# ----- Order creation ---------------------------------------------------

@transaction.atomic
def create_order_from_cart(
    dj_user,
    cart_items: Iterable[Mapping[str, object]],
) -> Order:
    """
    Create Order + OrderItem rows from [{'sku': 'ABC', 'qty': 2}, ...].
    Stores money rounded to 2dp using Order.q2.
    """
    app_user = _resolve_app_user(dj_user)

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

# ----- Payments & Status ------------------------------------------------

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
        set_order_status(order, "paid")

    return payment


ALLOWED_TRANSITIONS = {
    "pending":   {"paid", "cancelled"},
    "paid":      {"shipped"},
    "shipped":   {"delivered"},
    "delivered": set(),    
    "cancelled": set(),    
}
CANON = set(ALLOWED_TRANSITIONS.keys())


def allowed_next_statuses(current: str) -> list[str]:
    cur = (current or "").lower()
    return sorted(ALLOWED_TRANSITIONS.get(cur, set()))


def set_order_status(order: Order, to_status: str, by_user=None) -> OrderStatusHistory:
    """Validate and perform status transition, then write a history row."""
    frm = (order.status or "").lower()
    to = (to_status or "").lower()
    if to not in CANON:
        raise ValueError(f"Unknown status: {to}")
    allowed = ALLOWED_TRANSITIONS.get(frm, set())
    if to not in allowed:
        raise ValueError(f"Transition {frm} → {to} not allowed")

    # Update order
    order.status = to
    order.save(update_fields=["status"])

    # History
    hist = OrderStatusHistory.objects.create(
        order=order, from_status=frm, to_status=to, changed_by=by_user
    )
    return hist
