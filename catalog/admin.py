from django.contrib import admin
from .models import Product, Category, Brand

# Register your models here.
from django.contrib import admin
from .models import Product, Category, Brand

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "sku", "price", "stock", "is_active", "category", "brand")
    list_filter = ("is_active", "category", "brand")
    search_fields = ("name", "sku", "brand__name", "category__name")
    ordering = ("-id",)
    autocomplete_fields = ("category", "brand")

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "display_name", "slug")
    search_fields = ("name", "display_name", "slug")

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug")
    search_fields = ("name", "slug")
