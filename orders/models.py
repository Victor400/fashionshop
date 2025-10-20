# orders/models.py
from decimal import Decimal, ROUND_HALF_UP
from django.conf import settings
from django.db import models
from django.utils import timezone  # for created_at default

SCHEMA = "fashionshop"  # schema from DB

class Order(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        db_column="user_id",
        related_name="orders",
    )
    status = models.CharField(max_length=20, db_column="status", default="pending")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, db_column="total_amount")
    # Ensure NOT NULL inserts even though the table is unmanaged
    created_at = models.DateTimeField(db_column="created_at", default=timezone.now, editable=False)

    class Meta:
        db_table = f'"{SCHEMA}"."order"'
        managed = False 

    def __str__(self):
        return f"Order #{self.pk} ({self.status})"

    @staticmethod
    def q2(x: Decimal) -> Decimal:
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
        managed = False  # existing table

    def __str__(self):
        return f"{self.product_id} x{self.quantity}"

    @property
    def line_total(self):
        return Order.q2(Decimal(self.price_each) * self.quantity)
