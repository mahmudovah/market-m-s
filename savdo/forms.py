from django import forms

from kassa.models import CashAccount
from toifa.models import Product


class POSSaleForm(forms.Form):
    customer_name = forms.CharField(label="Mijoz", max_length=150, required=False)
    product = forms.ModelChoiceField(label="Mahsulot", queryset=Product.objects.filter(is_active=True))
    quantity = forms.DecimalField(label="Miqdor", min_value=0.001, decimal_places=3, max_digits=14)
    unit_price = forms.DecimalField(label="Sotuv narxi", min_value=0, decimal_places=2, max_digits=14)
    cash_account = forms.ModelChoiceField(label="Kassa hisobi", queryset=CashAccount.objects.all(), required=False)
    note = forms.CharField(label="Izoh", max_length=255, required=False)

