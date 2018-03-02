from django.contrib import admin
from .models import Wallet, Cryptocurrency, SiteSettings, Transaction
from .models import PaymentProvider, UserExternalWalletAddress
from .models import UserPaymentMethod, Order, UserWallet
from .models import UserWalletTransaction

admin.site.register(Wallet)
admin.site.register(Cryptocurrency)
admin.site.register(SiteSettings)
admin.site.register(PaymentProvider)
admin.site.register(UserExternalWalletAddress)
admin.site.register(UserPaymentMethod)
admin.site.register(Order)
admin.site.register(UserWallet)
admin.site.register(UserWalletTransaction)
