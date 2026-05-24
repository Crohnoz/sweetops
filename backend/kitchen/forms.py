from django import forms
from products.models import Product


class QuickOrderForm(forms.Form):
    customer_name = forms.CharField(
        required=False,
        label="Cliente"
    )

    notes = forms.CharField(
        required=False,
        widget=forms.Textarea,
        label="Notas"
    )

    products = forms.ModelMultipleChoiceField(
        queryset=Product.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )