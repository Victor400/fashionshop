from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=120)
    display_name = models.CharField(max_length=120, blank=True, null=True)
    slug = models.SlugField(max_length=140, unique=True)

    class Meta:
        db_table = "category"
        managed = False
        ordering = ["display_name", "name"]

    def __str__(self):
        return self.display_name or self.name


class Brand(models.Model):
    name = models.CharField(max_length=160, unique=True)
    slug = models.SlugField(max_length=180, unique=True)

    class Meta:
        db_table = "brand"
        managed = False
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True)
    sku = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField()

    # IMPORTANT: real FKs mapped to existing DB columns
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT,
        db_column="category_id", related_name="products"
    )
    brand = models.ForeignKey(
        Brand, on_delete=models.PROTECT,
        db_column="brand_id", related_name="products"
    )

    class Meta:
        db_table = "product"
        managed = False

    def __str__(self):
        return f"{self.name} ({self.sku})"
