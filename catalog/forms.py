from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name", "slug", "sku", "description",
            "price", "stock", "is_active", "category", "brand",
        ]

    def clean_price(self):
        price = self.cleaned_data["price"]
        if price is None or price < 0:
            raise forms.ValidationError("Price must be zero or greater.")
        return price

    def clean_stock(self):
        stock = self.cleaned_data["stock"]
        if stock is None or stock < 0:
            raise forms.ValidationError("Stock must be zero or greater.")
        return stock
