from django.contrib import admin
from .models import Wallet, Cryptocurrency, SiteSettings, Transaction
from .models import PaymentProvider, UserExternalWalletAddress
from .models import UserPaymentMethod, UserPaymentMethodImage, Order, UserWallet
from .models import UserWalletTransaction

class UserPaymentMethodAdmin(admin.ModelAdmin):
    def provider(self, obj):
        return obj.provider.code

    def user(self, obj):
        return obj.user.username

    def account_at_provider(self, obj):
        return obj.account_at_provider

    def account_alias(self, obj):
        return obj.account_alias

    def client_id(self, obj):
        return obj.client_id

    def client_secret(self, obj):
        return obj.client_secret

    list_display=('provider',
        'user', 
        'provider_qrcode_image',
        'account_at_provider', 
        'account_alias', 
        'client_id','client_secret')

    search_fields=['user__username']

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
