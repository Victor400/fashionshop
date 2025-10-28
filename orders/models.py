# orders/models.py
from decimal import Decimal, ROUND_HALF_UP
from django.conf import settings
from django.db import models
from django.utils import timezone


class AppUser(models.Model):
    """
    Simple user shadow table (only if you really need it);
    otherwise you can drop this and use settings.AUTH_USER_MODEL directly.
    """
    email = models.TextField()
    full_name = models.CharField(max_length=120, blank=True, null=True)
    created_at = models.DateTimeField()

    def __str__(self) -> str:
        return self.email or f"app_user:{self.pk}"


class Order(models.Model):
    user = models.ForeignKey(
        AppUser, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="orders",
    )
    status = models.CharField(max_length=20, default="pending")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    # ── Buyer & shipping fields ─────────────────────────
    buyer_name = models.TextField(blank=True, null=True)
    buyer_email = models.TextField(blank=True, null=True)
    buyer_phone = models.TextField(blank=True, null=True)

    ship_address1 = models.TextField(blank=True, null=True)
    ship_address2 = models.TextField(blank=True, null=True)
    ship_city = models.TextField(blank=True, null=True)
    ship_postcode = models.TextField(blank=True, null=True)
    ship_country = models.TextField(blank=True, null=True)

    notes = models.TextField(blank=True, null=True)
    # ───────────────────────────────────────────────────

    def __str__(self) -> str:
        return f"Order #{self.pk} ({self.status})"

    @staticmethod
    def q2(x: Decimal) -> Decimal:
        """Quantize to 2dp (HALF_UP)."""
        return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    price_each = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self) -> str:
        return f"{self.product_id} x{self.quantity}"

    @property
    def line_total(self) -> Decimal:
        return Order.q2(Decimal(self.price_each) * self.quantity)


class Payment(models.Model):
    class Method(models.TextChoices):
        CARD = "card", "Card"
        PAYPAL = "paypal", "PayPal"
        COD = "cod", "Cash on Delivery"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCESS = "successful", "Successful"
        FAILED = "failed", "Failed"

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payments")
    provider = models.CharField(max_length=40)
    method = models.CharField(max_length=20, choices=Method.choices)
    status = models.CharField(max_length=20, choices=Status.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    provider_ref = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    def __str__(self) -> str:
        return f"Payment #{self.pk} {self.provider}/{self.method} {self.status} £{self.amount}"


class OrderStatusHistory(models.Model):
    """
    Records every status change for an order.
    Django will create this table in the default schema (public).
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="status_history")
    from_status = models.CharField(max_length=20)
    to_status   = models.CharField(max_length=20)
    changed_by  = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="order_status_changes"
    )
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.order_id}: {self.from_status} → {self.to_status}"
