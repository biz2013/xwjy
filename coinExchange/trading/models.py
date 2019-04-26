from django.core.cache import cache
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

def user_payment_method_image_filename(instance, filename):
   return "uploads/paymentmethod/{0}/{1}_{2}".format(instance.provider.code, instance.user.id, filename)

def user_payment_method_tag_image_filename(instance, filename):
   return "uploads/paymentmethod/{0}/{1}_{2}_{3}".format(
      instance.user_payment_method.provider.code, 
      instance.user_payment_method.user.id, 
      instance.image_tag, filename)

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
    heepay_notify_url_host = models.CharField(max_length=128,default='localhost')
    heepay_notify_url_port = models.IntegerField(default=8000)
    heepay_return_url_host = models.CharField(max_length=128,default='localhost')
    heepay_return_url_port = models.IntegerField(default=8000)
    heepay_app_id= models.CharField(max_length=128)
    heepay_app_key= models.CharField(max_length=128)
    heepay_expire_in_sec = models.IntegerField(default=300)
    axfd_path= models.CharField(max_length=255, default='')
    axfd_datadir = models.CharField(max_length=255, default='')
    axfd_account_name = models.CharField(max_length=64, blank=True, default='')
    axfd_list_trans_count = models.IntegerField(default=1000)
    min_trx_confirmation = models.IntegerField(default=8)
    per_transaction_limit = models.IntegerField(default=100)
    axfd_passphrase = models.CharField(max_length=64, blank=True, default='')
    order_timeout_insec = models.IntegerField(default=600)
    confirmation_timeout_insec = models.IntegerField(default=300)
    config_json = models.CharField(max_length=8192, default='{}')

class GlobalCounter(models.Model):
    counter = models.IntegerField(default=0)
    lastupdated_at = models.DateTimeField(auto_now=True, null=True)
    lastupdated_by = models.CharField(max_length=32)

class PaymentProvider(models.Model):
   code = models.CharField(max_length=32, primary_key=True)
   name = models.CharField(max_length=32)
   config_json = models.CharField(max_length=8192, default='{}')
   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.ForeignKey(User, related_name='PaymentProvider_created_by', on_delete=models.SET_NULL, null=True)
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.ForeignKey(User, related_name='PaymentProvider_lastupdated_by', on_delete=models.SET_NULL, null=True)

class UserProfile(models.Model):
   user = models.OneToOneField(User, on_delete=models.CASCADE)
   alias = models.CharField(max_length=100, default='')

class UserPaymentMethod(models.Model):
   user = models.ForeignKey(User, on_delete=models.CASCADE)
   provider = models.ForeignKey('PaymentProvider', on_delete=models.CASCADE)
   account_at_provider = models.CharField(max_length=128, default='', null=True)
   account_alias = models.CharField(max_length=64, default='', null=True)
   client_id = models.CharField(max_length=128, default='')
   client_secret = models.CharField(max_length=256, default='')
   provider_qrcode_image = models.ImageField(upload_to=user_payment_method_image_filename)
   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.ForeignKey(User, related_name='UserPaymentMethod_created_by', on_delete=models.SET_NULL, null=True)
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.ForeignKey(User, related_name='UserPaymentMethod_lastupdated_by', on_delete=models.SET_NULL, null=True)

# most user payment method will have its main image and this is for
# extra image used for each payment method, if applicable.  So not every
# payment method need this.
class UserPaymentMethodImage(models.Model):
   IMAGE_TAG=(('WXSHOPASSTQRCODE', '小账本店员二维码'),
              ('OTHER','其他'))
   user_payment_method = models.ForeignKey('UserPaymentMethod', on_delete=models.CASCADE)
   image_tag = models.CharField(max_length=64, choices=IMAGE_TAG, null=False)
   qrcode = models.ImageField(upload_to=user_payment_method_tag_image_filename)
   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.ForeignKey(User, related_name='UserPaymentMethodImage_created_by', on_delete=models.SET_NULL, null=True)
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.ForeignKey(User, related_name='UserPaymentMethodImage_lastupdated_by', on_delete=models.SET_NULL, null=True)


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
        ('AUTOREDEEM','AutoRedeem'),
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
   user = models.ForeignKey(User, on_delete=models.CASCADE)
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
   SUBORDER_TYPE = (('OPEN','Open'), ('BUY_ON_ASK', 'Buy_on_ask'), ('SELL_ON_BID', 'Sell_on_bid'), 
                    ('ALL_OR_NOTHING', 'All_or_nothing'))

   ORDER_SOURCE_TYPE = (('TRADESITE', 'TradeSite'), ('API', 'API'))
   # These are not necessarily final, but I think so far we need these
   ORDER_STATUS = (('OPEN','Open'),('CANCELLED','Cancelled'), ('FILLED','Filled'),
            ('PAYING','Paying'), ('PAID','Paid'), ('FAILED', 'Failed'),
            ('DELIVERED','Delivered'),('PARTIALFILLED','PartialFilled'),('LOCKED','Locked'),
            ('BADACCOUNT', 'BADACCOUNT'))
   CURRENCY = (('CYN', 'Renminbi'), ('USD', 'US Dollar'), ('CAD', 'Canadian dollar'))

   order_id = models.CharField(max_length=64, primary_key=True)
   user = models.ForeignKey(User, on_delete=models.CASCADE)

   # purchase order only, this is the order # of the sell order it
   # buy from
   reference_order = models.ForeignKey('self', on_delete=models.SET_NULL, null=True)
   cryptocurrency = models.ForeignKey('Cryptocurrency', on_delete=models.SET_NULL, null=True)

   # payment provider picked by purchase order, purchase order only
   # NOTE: this is legacy and in the future it will have to match the payment provider
   #       dictated by seller.  And these may not be used if we use manual payment, not
   #       automatic API call
   selected_payment_provider = models.ForeignKey('PaymentProvider', on_delete=models.SET_NULL, null=True)
   account_at_selected_payment_provider = models.CharField(max_length=64, null=True)

   # payment provider picked by sell order and sell order only
   seller_payment_method = models.ForeignKey(UserPaymentMethod, on_delete=models.SET_NULL, null=True)

   order_type = models.CharField(max_length=32, choices=ORDER_TYPE)
   sub_type = models.CharField(max_length=32, default='OPEN', choices=SUBORDER_TYPE)
   order_source = models.CharField(max_length=32, choices= ORDER_SOURCE_TYPE, default='TRADESITE')
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

   # the out_order_no in api call that associated with this order
   api_call_reference_order_id = models.CharField(max_length=64, null=True)
   status = models.CharField(max_length=32, choices=ORDER_STATUS)

   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.ForeignKey(User, related_name='Order_created_by', on_delete=models.SET_NULL, null=True)
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.ForeignKey(User, related_name='Order_lastupdated_by', on_delete=models.SET_NULL, null=True)

class Transaction(models.Model) :
   TRANS_TYPES= (('BUY_ON_ASK','BUY_ON_ASK'), ('SELL_ON_BID', 'SELL_ON_BID'),
         ('SELLER_TRANSFER_AXFUND','SELLER_TRANSFER_AXFUND'),
         ('USER_WITHDRAW_AXFUND', 'USER_WITHDRAW_AXFUND'),
         ('DEPOSIT_AXFUND', 'DEPOSIT_AXFUND'),
         ('BUYER_PREPARE_ORDER_FOR_PAYMENT', 'BUYER_PREPARE_ORDER_FOR_PAYMENT'),
         ('PAYMENT_CONFIRM_NOTIFIED', 'PAYMENT_CONFIRM_NOTIFIED'),
         ('UPDATE_OTHER_TRANS', 'UPDATE_OTHER_TRANS'))
   TRANS_STATUS = (('SUCCEED','SUCCESS'),
         ('FAILED','FAILED'))
   transactionId = models.CharField(primary_key=True, max_length=64)
   transactionType = models.CharField(max_length=64, choices=TRANS_TYPES)
   buy_order = models.ForeignKey('Order', on_delete=models.SET_NULL, null = True, related_name='trans_buy_order')
   sell_order = models.ForeignKey('Order', on_delete=models.SET_NULL, null = True, related_name='trans_sell_order')
   axf_txId = models.CharField(max_length=128, null = True)
   fromUser = models.ForeignKey(User, on_delete=models.SET_NULL, null = True, related_name='trans_fromuser')
   fromUser_paymentmethod = models.ForeignKey('UserPaymentMethod', on_delete=models.SET_NULL, null = True, related_name='trans_fromuser_paymentmethod')
   toUser = models.ForeignKey(User, on_delete=models.SET_NULL, null = True, related_name='trans_touser')
   toUser_paymentmethod = models.ForeignKey('UserPaymentMethod', on_delete=models.SET_NULL, null = True, related_name='trans_touser_paymentmethod')
   reference_trans = models.ForeignKey('Transaction', on_delete=models.SET_NULL, null = True)
   units = models.FloatField(default=0)
   unit_price = models.FloatField(default=0)
   total = models.FloatField(default=0)
   fees = models.FloatField(default=0)
   status = models.CharField(max_length=32, choices=TRANS_STATUS)
   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.ForeignKey(User, related_name='trans_created_by', on_delete=models.SET_NULL, null=True)
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.ForeignKey(User, related_name='trans_lastupdated_by', on_delete=models.SET_NULL, null=True)

class OrderChangeLog(models.Model):
   order_action = (('OPEN_PAYMENT', 'Open_Payment'),
      ('OPEN_PAYMENT_FAILURE','Open_Payment_Failure'),
      ('PAYMENT_PROCESSING','Payment_Processing'),
      ('PAYMENT_SUCCESS', 'Payment_Success'),
      ('FUND_DELIVERED','Fund_Delivered')
      )
   order = models.ForeignKey('Order', on_delete=models.CASCADE)
   action = models.CharField(max_length = 32, choices=order_action)
   amount = models.FloatField(default=0.0)
   message = models.CharField(max_length = 1024)
   timestamp = models.DateTimeField()

# This is to save json data that relate to cronjob,
#
class CronJobData(models.Model):
   jobname =  models.CharField(max_length=64, primary_key=True)
   last_run_at_timestamp = models.IntegerField(default=0)
   data = models.CharField(max_length=1024, default='{}')
   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.ForeignKey(User, related_name='cron_created_by', on_delete=models.SET_NULL, null=True)
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.ForeignKey(User, related_name='cron_lastupdated_by', on_delete=models.SET_NULL, null=True)
