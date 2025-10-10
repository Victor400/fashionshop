from django.db import models


class Category(models.Model):
    """Maps to fashionshop.category"""
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
    """Maps to fashionshop.brand"""
    name = models.CharField(max_length=160, unique=True)
    slug = models.SlugField(max_length=180, unique=True)

    class Meta:
        db_table = "brand"
        managed = False
        ordering = ["name"]

    def __str__(self):
        return self.name
