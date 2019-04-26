from django import forms

from trading.models import UserPaymentMethodImage

class UserPaymentMethodImageForm(forms.ModelForm):
    class Meta:
        model = UserPaymentMethodImage
        fields = ('id', 'user_payment_method', 'image_tag', 'qrcode', 'created_by', 'lastupdated_by')