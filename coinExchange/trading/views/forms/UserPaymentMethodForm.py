from django import forms

from trading.models import UserPaymentMethod

class UserPaymentMethodForm(forms.ModelForm):
    class Meta:
        model = UserPaymentMethod
        fields = ('id', 'account_at_provider', 'account_alias', 'user', 'provider', 'created_by', 'lastupdated_by')