from django.core.cache import cache
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class SingletonModel(models.Model):

    class Meta:
        abstract = True

    def set_cache(self):
        cache.set(self.__class__.__name__, self)

    def save(self, *args, **kwargs):
        self.pk = 1
        super(SingletonModel, self).save(*args, **kwargs)
        self.set_cache()

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        if cache.get(cls.__name__) is None:
            obj, created = cls.objects.get_or_create(pk=1)
            if not created:
                obj.set_cache()
        return cache.get(cls.__name__)

# Global site settings.
class SiteSettings(SingletonModel):
    support = models.EmailField(default='support@example.com')
    heepay_app_id= models.CharField(max_length=128)
    heepay_app_key= models.CharField(max_length=128)
    axfd_passphrase = models.CharField(max_length=64, blank=True, default='')

class PaymentProvider(models.Model):
   code = models.CharField(max_length=32, primary_key=True)
   name = models.CharField(max_length=32)
   config_json = models.TextField()
   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.ForeignKey(User, related_name='PaymentProvider_created_by', on_delete=models.SET_NULL, null=True)
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.ForeignKey(User, related_name='PaymentProvider_lastupdated_by', on_delete=models.SET_NULL, null=True)


class UserPaymentMethod(models.Model):
   user = models.ForeignKey(User, on_delete=models.CASCADE)
   provider = models.ForeignKey('PaymentProvider', on_delete=models.CASCADE)
   account_at_provider = models.CharField(max_length=64)
   provider_qrcode_image = models.ImageField(upload_to='uploads/')
   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.ForeignKey(User, related_name='UserPaymentMethod_created_by', on_delete=models.SET_NULL, null=True)
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.ForeignKey(User, related_name='UserPaymentMethod_lastupdated_by', on_delete=models.SET_NULL, null=True)


class Cryptocurrency(models.Model):
   currency_code = models.CharField(max_length=16, primary_key=True)
   name = models.CharField(max_length=32)
   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.ForeignKey(User, related_name='Cryptocurrency_created_by', on_delete=models.SET_NULL, null=True)
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.ForeignKey(User, related_name='Cryptocurrency_lastupdated_by', on_delete=models.SET_NULL, null=True)

class Wallet(models.Model):
   name = models.CharField(max_length=32, unique=True, default='first')
   cryptocurrency = models.ForeignKey('Cryptocurrency', on_delete=models.CASCADE)
   config_json = models.TextField()
   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.ForeignKey(User, related_name='Wallet_created_by', on_delete=models.SET_NULL, null=True)
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.ForeignKey(User, related_name='Wallet_lastupdated_by', on_delete=models.SET_NULL, null=True)

class UserWallet(models.Model):
   user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
   wallet = models.ForeignKey('Wallet', on_delete=models.CASCADE)
   # refer the to last user wallet transaction record's id, which is the
   # transaction that gives the latest update. Not make it foreign key to
   # avoid circular dependencys
   user_wallet_trans_id = models.IntegerField(null=True)
   wallet_addr = models.CharField(max_length=128)
   balance = models.FloatField(default=0.0)
   locked_balance = models.FloatField(default=0.0)
   available_balance = models.FloatField(default=0.0)
   last_closed_sellorder_id = models.CharField(max_length=128, null=True)
   last_closed_buyorder_id = models.CharField(max_length=128, null=True)
   last_wallet_trxId = models.CharField(max_length=128, default='')
   last_wallet_timestamp = models.IntegerField(default=0)
   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.ForeignKey(User, related_name='UserWallet_created_by', on_delete=models.SET_NULL, null=True)
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.ForeignKey(User, related_name='UserWallet_lastupdated_by', on_delete=models.SET_NULL, null=True)

class UserWalletTransaction(models.Model):
   BALANCE_UPDATE_TYPES = (('CREDIT','Credit'),('DEBT','Debt'))
   TRANS_TYPES =(('OPEN BUY ORDER', 'Open Buy Order'),
        ('OPEN SELL ORDER', 'Open Sell Order'),
        ('CANCEL SELL ORDER', 'Cancel Sell Order'),
        ('CANCEL BUY ORDER', 'Cancel Buy Order'),
        ('DELIVER ON PURCHASE', 'Deliver on purhcase'),
        ('REDEEM','Redeem'), ('REDEEMFEE', 'RedeemFee'),
        ('DEPOSIT','Deposit'))
   TRANS_STATUS = (('PENDING','Pending'), ('PROCESSED','Processed'), ('CANCELLED', 'Cancelled'))
   # status for automatic payment
   PAYMENT_STATUS = (('NOTSTATRTED', 'Not Started'),
     ('PAYSUCCESS', 'PaySuccess'),
     ('SUCCESS','Success'),
     ('EXPIREDINVALID', 'ExpiredInvalid'),
     ('DEVCLOSE', 'DevClose'),
     ('USERABANDON', 'UserAbandon'),
     ('UNKONWN','UnKnown'),
     ('FAILURE','Failure'),
     ('STARTING', 'Starting'))
   user_wallet = models.ForeignKey('UserWallet', on_delete=models.CASCADE)
   balance_begin = models.FloatField(default=0.0)
   balance_end = models.FloatField(default=0.0)
   locked_balance_begin = models.FloatField(default=0.0)
   locked_balance_end = models.FloatField(default=0.0)
   available_to_trade_begin = models.FloatField(default=0.0)
   available_to_trade_end = models.FloatField(default=0.0)

   # if the transaction is related to an order, put order # here
   reference_order = models.ForeignKey('Order', on_delete=models.CASCADE, null=True)

   # if the transaction is related to deposite or redeem, put wallet
   # txid here
   reference_wallet_trxId = models.CharField(max_length=128, default='')
   units = models.FloatField(default=0.0)
   balance_update_type= models.CharField(max_length=32, choices=BALANCE_UPDATE_TYPES)
   transaction_type = models.CharField(max_length=32, choices=TRANS_TYPES)
   # payment provider
   payment_provider = models.ForeignKey('PaymentProvider', on_delete=models.SET_NULL, null=True)
   # bill no of the associated payment.
   payment_bill_no = models.CharField(max_length=128, null=True)
   # status of the associated payment.
   payment_status = models.CharField(max_length=64, choices=PAYMENT_STATUS, default='UNKNOWN')
   # fiat money amount for the payment transaction

   fiat_money_amount = models.FloatField(default=0.0)
   comment = models.CharField(max_length=2048, null = True)
   reported_timestamp = models.IntegerField(default =0)
   status = models.CharField(max_length=32, choices = TRANS_STATUS)
   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.ForeignKey(User, related_name='UserWallet_trans_created_by', on_delete=models.SET_NULL, null=True)
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.ForeignKey(User, related_name='UserWallet_trans_lastupdated_by', on_delete=models.SET_NULL, null=True)

class UserExternalWalletAddress(models.Model):
   user = models.ForeignKey('User', on_delete=models.CASCADE)
   cryptocurrency = models.ForeignKey('Cryptocurrency', on_delete=models.CASCADE)
   address = models.CharField(max_length=128)
   alias = models.CharField(max_length=32, null=True)
   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.ForeignKey(User, related_name='UserExternalWalletAddress_created_by', on_delete=models.SET_NULL, null=True)
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.ForeignKey(User, related_name='UserExternalWalletAddress_lastupdated_by', on_delete=models.SET_NULL, null=True)

class UserStatue(models.Model):
   user = models.ForeignKey(User, on_delete=models.CASCADE)
   avg_score = models.FloatField()
   trans_count = models.IntegerField()
   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.ForeignKey(User, related_name='UserStatue_created_by', on_delete=models.SET_NULL, null=True)
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.ForeignKey(User, related_name='UserStatue_lastupdated_by', on_delete=models.SET_NULL, null=True)

class Order(models.Model):
   ORDER_TYPE = (('BUY','Buy'),('SELL','Sell'),('REDEEM','Redeem'))

   #buy_on_ask and sell_on_bid are for future automatic trading for the games
   SUBORDER_TYPE = (('OPEN','Open'), ('BUY_ON_ASK', 'Buy_on_ask'), ('SELL_ON_BID', 'Sell_on_bid'))

   # These are not necessarily final, but I think so far we need these
   ORDER_STATUS = (('OPEN','Open'),('CANCELLED','Cancelled'), ('FILLED','Filled'),
            ('PAYING','Paying'), ('PAID','Paid'), ('FAILED', 'Failed'),
            ('DELIVERED','Delivered'),('PARTIALFILLED','PartialFilled'),('LOCKED','Locked'))
   CURRENCY = (('CYN', 'Renminbi'), ('USD', 'US Dollar'))

   order_id = models.CharField(max_length=64, primary_key=True)
   user = models.ForeignKey(User, on_delete=models.CASCADE)

   # purchase order only, this is the order # of the sell order it
   # buy from
   reference_order = models.ForeignKey('self', on_delete=models.SET_NULL, null=True)
   cryptocurrency = models.ForeignKey('Cryptocurrency', on_delete=models.SET_NULL, null=True)

   # payment provider picked by purchase order, purchase order only
   selected_payment_provider = models.ForeignKey('PaymentProvider', on_delete=models.SET_NULL, null=True)

   order_type = models.CharField(max_length=32, choices=ORDER_TYPE)
   sub_type = models.CharField(max_length=32, default='OPEN', choices=SUBORDER_TYPE)
   units = models.FloatField()
   unit_price = models.FloatField()
   unit_price_currency = models.CharField(max_length = 8, choices=CURRENCY, default='CYN')
   #We use lock count to verify whether there's buy order lock on the
   #sell order
   lock_count = models.IntegerField(default=0)

   #how many units is being purchased(not paid) by buyers
   units_locked = models.FloatField(default=0.0)
   # units - paid units - units being bought but not paid (locked)
   units_available_to_trade = models.FloatField(default=0.0)

   # the total amount of original units x unit price, used by
   # purchase order. To the two decimal places
   total_amount = models.FloatField(default = 0.0)
   status = models.CharField(max_length=32, choices=ORDER_STATUS)

   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.ForeignKey(User, related_name='Order_created_by', on_delete=models.SET_NULL, null=True)
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.ForeignKey(User, related_name='Order_lastupdated_by', on_delete=models.SET_NULL, null=True)

class UserProfile(models.Model):
   USER_TYPE = (('TRADEUSER', 'TradeUser'), ('APIUSER', 'APIUser'))
   user = models.ForeignKey(User, on_delete=models.CASCADE)
   user_type = models.CharField(max_length=32, choices=USER_TYPE, default='TRADEUSER')
   api_key = models.CharField(max_length=128, default='')
   api_secret = models.CharField(max_length=128, default='')

   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.ForeignKey(User, related_name='UserProfile_created_by', on_delete=models.SET_NULL, null=True)
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.ForeignKey(User, related_name='UserProfile_lastupdated_by', on_delete=models.SET_NULL, null=True)
    
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
    notify_url = models.CharField(max_length=1024, null=True)
    return_url = models.CharField(max_length=1024, null=True)
    last_notify = models.CharField(max_length=2048, null=True)
    last_notify_response = models.CharField(max_length=16, null=True)
    last_notified_at = models.DateTimeField(auto_now_add=False, null=True)
    last_status_description = models.CharField(max_length=1024, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name='APIUserTransaction_created_by', on_delete=models.SET_NULL, null=True)
    lastupdated_at = models.DateTimeField(auto_now=True)
    lastupdated_by = models.ForeignKey(User, related_name='APIUserTransaction_lastupdated_by', on_delete=models.SET_NULL, null=True)        