from django.db import models
from django.contrib.auth.models import User
from trading.models import Cryptocurrency,PaymentProvider,Order

# Create your models here.

class APIUserAccount(models.Model):
    ACCOUNT_STATUS =(('OPEN', 'Open'),
        ('ACTIVE', 'Active'),
        ('PENDING', 'Pending'),
        ('SUSPENDED', 'Suspended'),
        ('CLOSED', 'Closed'))
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    accountNo = models.CharField(max_length=32, unique=True)
    apiKey = models.CharField(max_length=128, primary_key=True)
    secretKey = models.CharField(max_length=128, unique=True)
    status = models.CharField(max_length=32, choices=ACCOUNT_STATUS)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name='APIUserAccount_created_by', on_delete=models.SET_NULL, null=True)
    lastupdated_at = models.DateTimeField(auto_now=True)
    lastupdated_by = models.ForeignKey(User, related_name='APIUserAccount_lastupdated_by', on_delete=models.SET_NULL, null=True)

class APIUserExternalWalletAddress(models.Model):
    api_account = models.OneToOneField(APIUserAccount, on_delete=models.CASCADE)
    cryptocurrency = models.ForeignKey('trading.Cryptocurrency', on_delete=models.CASCADE)
    address = models.CharField(max_length=128)
    alias = models.CharField(max_length=32, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name='APIUserExternalWalletAddress_created_by', on_delete=models.SET_NULL, null=True)
    lastupdated_at = models.DateTimeField(auto_now=True)
    lastupdated_by = models.ForeignKey(User, related_name='APIUserExternalWalletAddress_lastupdated_by', on_delete=models.SET_NULL, null=True)

class APIUserTransaction(models.Model):
    TRADE_STATUS=(
        ('UNKNOWN', 'Unknown'),
        ('NOTSTATED', 'NotStarted'),
        ('INPROGRESS', 'InProgress'),
        ('PAIDSUCCESS','PaidSuccess'),
        ('SUCCESS','Success'),
        ('SYSTEMERROR', 'SystemError'),
        ('USERCANCELLED', 'UserCancelled'),
        ('EXPIRED', 'Expired')
    )
    transactionId = models.CharField(max_length=128, primary_key=True)
    api_user = models.ForeignKey(APIUserAccount, on_delete=models.CASCADE)
    payment_provider = models.ForeignKey(PaymentProvider, on_delete=models.CASCADE)
    reference_order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True)
    payment_account = models.CharField(max_length=32, null=True)
    action = models.CharField(max_length=32)
    client_ip = models.CharField(max_length=20, null=True)
    subject = models.CharField(max_length=256, default='')
    total_fee = models.IntegerField(default=0)
    attach = models.CharField(max_length=1024, null=True)
    request_timestamp = models.CharField(max_length=32, null=True)
    original_request = models.CharField(max_length=2048)
    payment_provider_last_notify = models.CharField(max_length=4096, null=True, default=None)
    payment_provider_last_notified_at = models.DateTimeField(auto_now_add=False, null=True)
    expire_in_sec = models.IntegerField(default=600)
    status = models.CharField(max_length=32, choices=TRADE_STATUS)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name='APIUserTransaction_created_by', on_delete=models.SET_NULL, null=True)
    lastupdated_at = models.DateTimeField(auto_now=True)
    lastupdated_by = models.ForeignKey(User, related_name='APIUserTransaction_lastupdated_by', on_delete=models.SET_NULL, null=True)
