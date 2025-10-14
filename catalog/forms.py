from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name", "slug", "sku", "description",
            "price", "stock", "is_active", "category", "brand",
        ]
        error_messages = {
            "sku": {
                "unique": "A product with this SKU already exists.",
            },
            "slug": {
                "unique": "This URL slug is already in use.",
            },
        }

    def clean_price(self):
        price = self.cleaned_data["price"]
        if price is None or price <= 0:
            raise forms.ValidationError("Price must be greater than 0.")
        return price

    def clean_stock(self):
        stock = self.cleaned_data["stock"]
        if stock is None or stock < 0:
            raise forms.ValidationError("Stock cannot be negative.")
        return stock
