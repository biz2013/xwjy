from django.db import models
from django.contrib.auth.models import User
from trading.models import Cryptocurrency,PaymentProvider,Order, UserPaymentMethod

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
    # source: url of the 3rd party website, shows who is calling our api.
    source = models.CharField(max_length=128, null=True)
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
    PAYMENT_STATUS=(
        ('UNKNOWN', 'Unknown'),
        ('NOTSTARTED', 'Not Started'),
        ('STARTING', 'Starting'),
        ('PAYSUCCESS','PaySuccess'),
        ('SUCCESS','Success'),
        ('EXPIREDINVALID','ExpiredInvalid'),
        ('USERABANDON', 'UserAbandon'),
        ('DEVCLOSE', 'DevClose'),
        ('FAILURE', 'Failure')
    )
    TRADE_STATUS=(
        ('UNKNOWN', 'Unknown'),
        ('NOTSTARTED', 'Not Started'),
        ('INPROGRESS', 'InProgress'),
        ('PAIDSUCCESS','PaidSuccess'),
        ('SUCCESS','Success'),
        ('PAYFAILED', 'Pay Failed'),
        ('SYSTEMERROR', 'SystemError'),
        ('USERCANCELLED', 'UserCancelled'),
        ('EXPIRED', 'Expired')
    )
    transactionId = models.CharField(max_length=128, primary_key=True)
    api_out_trade_no = models.CharField(max_length=128, default='')
    api_user = models.ForeignKey(APIUserAccount, on_delete=models.CASCADE)
    payment_provider = models.ForeignKey(PaymentProvider, on_delete=models.CASCADE)
    reference_order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True)
    reference_bill_no = models.CharField(max_length=64, null=True)
    payment_account = models.CharField(max_length=32, null=True)
    # API seller pick payment method
    seller_payment_method = models.ForeignKey(UserPaymentMethod, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=32)
    client_ip = models.CharField(max_length=20, null=True)
    subject = models.CharField(max_length=256, default='')
    total_fee = models.IntegerField(default=0)
    real_fee = models.IntegerField(default=0)
    attach = models.CharField(max_length=1024, null=True)
    request_timestamp = models.CharField(max_length=32, null=True)
    original_request = models.CharField(max_length=2048)
    payment_provider_last_notify = models.CharField(max_length=4096, null=True, default=None)
    payment_provider_last_notified_at = models.DateTimeField(auto_now_add=False, null=True)
    expire_in_sec = models.IntegerField(default=600)
    payment_status = models.CharField(max_length=32, choices=PAYMENT_STATUS, default='UNKNOWN')
    trade_status = models.CharField(max_length=32, choices=TRADE_STATUS, default='UNKNOWN')
    external_cny_receive_addr = models.CharField(max_length=64, null=True, default=None)
    notify_url = models.CharField(max_length=1024, null=True)
    return_url = models.CharField(max_length=1024, null=True)
    last_notify = models.CharField(max_length=2048, null=True)
    last_notify_response = models.CharField(max_length=1024, null=True)
    last_notified_at = models.DateTimeField(auto_now_add=False, null=True)
    last_status_description = models.CharField(max_length=1024, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name='APIUserTransaction_created_by', on_delete=models.SET_NULL, null=True)
    lastupdated_at = models.DateTimeField(auto_now=True)
    lastupdated_by = models.ForeignKey(User, related_name='APIUserTransaction_lastupdated_by', on_delete=models.SET_NULL, null=True)
