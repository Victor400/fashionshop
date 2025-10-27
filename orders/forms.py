# orders/forms.py
from django import forms
from django.forms import ModelForm
from .models import Order
from .services import allowed_next_statuses

class CheckoutDetailsForm(ModelForm):
    class Meta:
        model = Order
        fields = [
            "buyer_name", "buyer_email", "buyer_phone",
            "ship_address1", "ship_address2", "ship_city",
            "ship_postcode", "ship_country",
            "notes",
        ]
        widgets = {
            "buyer_name":    forms.TextInput(attrs={"class": "form-control form-control-sm"}),
            "buyer_email":   forms.EmailInput(attrs={"class": "form-control form-control-sm"}),
            "buyer_phone":   forms.TextInput(attrs={"class": "form-control form-control-sm"}),

            "ship_address1": forms.TextInput(attrs={"class": "form-control form-control-sm"}),
            "ship_address2": forms.TextInput(attrs={"class": "form-control form-control-sm"}),
            "ship_city":     forms.TextInput(attrs={"class": "form-control form-control-sm"}),
            "ship_postcode": forms.TextInput(attrs={"class": "form-control form-control-sm"}),
            "ship_country":  forms.TextInput(attrs={"class": "form-control form-control-sm"}),

            # smaller textarea
            "notes":         forms.Textarea(attrs={"class": "form-control form-control-sm", "rows": 2}),
        }
        labels = {
            "buyer_name": "Full name",
            "buyer_email": "Email",
            "buyer_phone": "Phone",
            "ship_address1": "Address line 1",
            "ship_address2": "Address line 2",
            "ship_city": "City",
            "ship_postcode": "Postcode",
            "ship_country": "Country",
            "notes": "Notes for courier",
        }



class OrderStatusForm(forms.Form):
    to_status = forms.ChoiceField(label="New status")

    def __init__(self, *args, order: Order, **kwargs):
        super().__init__(*args, **kwargs)
        choices = [(s, s.title()) for s in allowed_next_statuses(order.status)]
        self.fields["to_status"].choices = choices
        if not choices:
            self.fields["to_status"].widget.attrs["disabled"] = True