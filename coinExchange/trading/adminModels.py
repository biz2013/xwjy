from django.contrib import admin
from .models import Wallet, Cryptocurrency, SiteSettings, Transaction
from .models import PaymentProvider, UserExternalWalletAddress
from .models import UserPaymentMethod, UserPaymentMethodImage, Order, UserWallet
from .models import UserWalletTransaction

class UserPaymentMethodImageAdmin(admin.ModelAdmin):
    def payment_method(self, obj):
        return obj.user_payment_method.provider.code

    def user_payment_method_user(self, obj):
        return obj.user_payment_method.user.username

    def user_payment_method_account(self, obj):
        return obj.user_payment_method.account_at_provider

    def user_payment_method_alias(self, obj):
        return obj.user_payment_method.account_alias

    def user_payment_method_client_id(self, obj):
        return obj.user_payment_method.client_id

    def user_payment_method_client_secret(self, obj):
        return obj.user_payment_method.client_secret

    list_display=('payment_method',
        'user_payment_method_user', 
        'user_payment_method_account', 
        'user_payment_method_alias', 
        'image_tag','qrcode',
        'user_payment_method_client_id',
        'user_payment_method_client_secret')

    search_fields=['user_payment_method__user__username']