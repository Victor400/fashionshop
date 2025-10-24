
from decimal import Decimal, ROUND_HALF_UP
from django.db import models
from django.utils import timezone

SCHEMA = "fashionshop"

class AppUser(models.Model):
    """Unmanaged mapping to fashionshop.app_user"""
    id = models.BigAutoField(primary_key=True, db_column="id")
    email = models.TextField(db_column="email")  # citext in DB
    full_name = models.CharField(max_length=120, db_column="full_name", blank=True, null=True)
    created_at = models.DateTimeField(db_column="created_at")

    class Meta:
        db_table = f'"{SCHEMA}"."app_user"'
        managed = False

    def __str__(self) -> str:
        return self.email or f"app_user:{self.pk}"

class Order(models.Model):
    user = models.ForeignKey(
        AppUser, null=True, blank=True,
        on_delete=models.SET_NULL,
        db_column="user_id",
        related_name="orders",
    )
    status = models.CharField(max_length=20, db_column="status", default="pending")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, db_column="total_amount")
    created_at = models.DateTimeField(db_column="created_at", default=timezone.now, editable=False)

    class Meta:
        db_table = f'"{SCHEMA}"."order"'
        managed = False

    def __str__(self) -> str:
        return f"Order #{self.pk} ({self.status})"

    @staticmethod
    def q2(x: Decimal) -> Decimal:
        """Quantize to 2dp with bankers' rounding disabled (HALF_UP)."""
        return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE,
        related_name="items", db_column="order_id"
    )
    product = models.ForeignKey(
        "catalog.Product", on_delete=models.PROTECT,
        db_column="product_id"
    )
    quantity = models.PositiveIntegerField(db_column="quantity")
    price_each = models.DecimalField(max_digits=10, decimal_places=2, db_column="price_each")

    class Meta:
        db_table = f'"{SCHEMA}"."order_item"'
        managed = False

    def __str__(self) -> str:
        return f"{self.product_id} x{self.quantity}"

    @property
    def line_total(self) -> Decimal:
        return Order.q2(Decimal(self.price_each) * self.quantity)


class Payment(models.Model):
    """
    Unmanaged mapping to fashionshop.payment.
    Postgres ENUMs:
      - fashionshop.payment_method:   'card', 'paypal', 'cod'
      - fashionshop.payment_status:   'pending', 'successful', 'failed'
    """
    class Method(models.TextChoices):
        CARD = "card", "Card"
        PAYPAL = "paypal", "PayPal"
        COD = "cod", "Cash on Delivery"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCESS = "successful", "Successful"
        FAILED = "failed", "Failed"

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE,
        related_name="payments", db_column="order_id"
    )
    provider = models.CharField(max_length=40, db_column="provider")  # e.g. 'stripe'
    method = models.CharField(max_length=20, choices=Method.choices, db_column="method")
    status = models.CharField(max_length=20, choices=Status.choices, db_column="status")
    amount = models.DecimalField(max_digits=10, decimal_places=2, db_column="amount")
    provider_ref = models.CharField(max_length=200, db_column="provider_ref", blank=True, null=True)
    created_at = models.DateTimeField(db_column="created_at", default=timezone.now, editable=False)

    class Meta:
        db_table = f'"{SCHEMA}"."payment"'
        managed = False

    def __str__(self) -> str:
        return f"Payment #{self.pk} {self.provider}/{self.method} {self.status} £{self.amount}"
