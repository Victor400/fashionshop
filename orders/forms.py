from django import forms
from .models import Order

class CheckoutDetailsForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            "buyer_name", "buyer_email", "buyer_phone",
            "ship_address1", "ship_address2", "ship_city",
            "ship_postcode", "ship_country", "notes",
        ]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
        }
