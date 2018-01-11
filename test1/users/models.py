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
    axfd_account_name = models.CharField(max_length=64, default='')
    axfd_list_trans_count = models.IntegerField(default=1000)
    min_trx_confirmation = models.IntegerField(default=8)

class GlobalCounter(models.Model):
    counter = models.IntegerField(default=0)
    lastupdated_at = models.DateTimeField(auto_now=True, null=True)
    lastupdated_by = models.CharField(max_length=32)

# class UserLogin(models.Model):
#    username = models.CharField(max_length=32, primary_key=True)
#    passwd_hash = models.CharField(max_length=64)
#    alias = models.CharField(max_length=64, default='')
#    config_json = models.CharField(max_length=4096)
#    created_at = models.DateTimeField(auto_now_add=True)
#    created_by = models.ForeignKey('self', on_delete = models.CASCADE, related_name="login_created_by", null = True)
#    lastupdated_at = models.DateTimeField(auto_now=True, null=True)
#    lastupdated_by = models.ForeignKey('self', on_delete=models.CASCADE, related_name="login_lastupdated_by", null = True)

class PaymentProvider(models.Model):
   code = models.CharField(max_length=32, primary_key=True)
   name = models.CharField(max_length=32)
   config_json = models.TextField()
   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.ForeignKey(User, related_name='PaymentProvider_created_by')
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.ForeignKey(User, related_name='PaymentProvider_lastupdated_by')

# class User(models.Model):
#    login = models.OneToOneField('UserLogin', on_delete= models.CASCADE, null=True)
#    firstname = models.CharField(max_length=32)
#    middle = models.CharField(max_length=32, default='')
#    lastname = models.CharField(max_length=32)
#    email = models.CharField(max_length=64)
#    phone = models.CharField(max_length=32, default='')
#    config_json = models.TextField(default='')
#    created_at = models.DateTimeField(auto_now_add=True)
#    created_by = models.ForeignKey('UserLogin', related_name='User_created_by')
#    lastupdated_at = models.DateTimeField(auto_now=True)
#    lastupdated_by = models.ForeignKey('UserLogin', related_name='User_lastupdated_by')

# User Profile, extension of auth.models.User
class Profile(models.Model):
   user = models.OneToOneField(User, on_delete=models.CASCADE)
   firstname = models.CharField(max_length=32)
   middle = models.CharField(max_length=32, default='')
   lastname = models.CharField(max_length=32)
   email = models.CharField(max_length=64)
   phone = models.CharField(max_length=32, default='')
   birth_date = models.DateField(null=True, blank=True)
   config_json = models.TextField(default='')
   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.ForeignKey(User, related_name='User_created_by')
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.ForeignKey(User, related_name='User_lastupdated_by')

# TODO: Chi, enable this later.
# define signals so our Profile model will be automatically created/updated
# when we create/update User instances.
# @receiver(post_save, sender=User)
# def create_user_profile(sender, instance, created, **kwargs):
#     if created:
#         Profile.objects.create(user=instance)
#
# @receiver(post_save, sender=User)
# def save_user_profile(sender, instance, **kwargs):
#     instance.profile.save()

class UserPaymentMethod(models.Model):
   user = models.ForeignKey(User, on_delete=models.CASCADE)
   provider = models.ForeignKey('PaymentProvider', on_delete=models.CASCADE)
   account_at_provider = models.CharField(max_length=64)
   provider_qrcode_image = models.ImageField(upload_to='uploads/')
   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.ForeignKey(User, related_name='UserPaymentMethod_created_by')
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.ForeignKey(User, related_name='UserPaymentMethod_lastupdated_by')


class Cryptocurrency(models.Model):
   currency_code = models.CharField(max_length=16, primary_key=True)
   name = models.CharField(max_length=32)
   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.ForeignKey(User, related_name='Cryptocurrency_created_by')
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.ForeignKey(User, related_name='Cryptocurrency_lastupdated_by')

class Wallet(models.Model):
   name = models.CharField(max_length=32, unique=True, default='first')
   cryptocurrency = models.ForeignKey('Cryptocurrency', on_delete=models.CASCADE)
   config_json = models.TextField()
   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.ForeignKey(User, related_name='Wallet_created_by')
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.ForeignKey(User, related_name='Wallet_lastupdated_by')

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
   created_by = models.ForeignKey(User, related_name='UserWallet_created_by')
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.ForeignKey(User, related_name='UserWallet_lastupdated_by')

class UserWalletTransaction(models.Model):
   BALANCE_UPDATE_TYPES = (('CREDIT','Credit'),('DEBT','Debt'))
   TRANS_TYPES =(('OPEN BUY ORDER', 'Open Buy Order'),
        ('OPEN SELL ORDER', 'Open Sell Order'),
        ('CANCEL SELL ORDER', 'Cancel Sell Order'),
        ('CANCEL BUY ORDER', 'Cancel Buy Order'),
        ('DELIVER ON PURCHASE', 'Deliver on purhcase'),
        ('REDEEM','Redeem'), ('DEPOSIT','Deposit'))
   TRANS_STATUS = (('PENDING','Pending'), ('PROCESSED','Processed'))
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
   amount = models.FloatField(default=0.0)
   balance_update_type= models.CharField(max_length=32, choices=BALANCE_UPDATE_TYPES)
   transaction_type = models.CharField(max_length=32, choices=TRANS_TYPES)
   comment = models.CharField(max_length=2048, null = True)
   reported_timestamp = models.IntegerField(default =0)
   status = models.CharField(max_length=32, choices = TRANS_STATUS)
   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.ForeignKey(User, related_name='UserWallet_trans_created_by')
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.ForeignKey(User, related_name='UserWallet_trans_lastupdated_by')

class UserExternalWalletAddress(models.Model):
   user = models.OneToOneField(User, on_delete=models.CASCADE)
   cryptocurrency = models.ForeignKey('Cryptocurrency', on_delete=models.CASCADE)
   address = models.CharField(max_length=128)
   alias = models.CharField(max_length=32, null=True)
   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.ForeignKey(User, related_name='UserExternalWalletAddress_created_by')
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.ForeignKey(User, related_name='UserExternalWalletAddress_lastupdated_by')

class UserStatue(models.Model):
   user = models.ForeignKey(User, on_delete=models.CASCADE)
   avg_score = models.FloatField()
   trans_count = models.IntegerField()
   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.ForeignKey(User, related_name='UserStatue_created_by')
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.ForeignKey(User, related_name='UserStatue_lastupdated_by')

class Order(models.Model):
   ORDER_TYPE = (('BUY','Buy'),('SELL','Sell'),('REDEEM','Redeem'))

   #buy_on_ask and sell_on_bid are for future automatic trading for the games
   SUBORDER_TYPE = (('OPEN','Open'), ('BUY_ON_ASK', 'Buy_on_ask'), ('SELL_ON_BID', 'Sell_on_bid'))

   # These are not necessarily final, but I think so far we need these
   ORDER_STATUS = (('OPEN','Open'),('CANCELLED','Cancelled'), ('FILLED','Filled'),
            ('PAYING','Paying'), ('PAID','Paid'),
            ('DELIVERED','Delivered'),('PARTIALFILLED','PartialFilled'),('LOCKED','Locked'))
   CURRENCY = (('CYN', 'Renminbi'), ('USD', 'US Dollar'))

   # status for automatic payment
   PAYMENT_STATUS = (('NOTSTATRTED', 'Not Started'),
     ('PAYSUCCESS', 'PaySuccess'),
     ('SUCCESS','Success'),
     ('EXPIREDINVALID', 'ExpiredInvalid'),
     ('DEVCLOSE', 'DevClose'),
     ('USERABANDON', 'UserAbandon'),
     ('UNKONW','UnKnow'),
     ('FAILURE','Failure'),
     ('STARTING', 'Starting'))
   order_id = models.CharField(max_length=64, primary_key=True)
   user = models.ForeignKey(User, on_delete=models.CASCADE)

   # purchase order only, this is the order # of the sell order it
   # buy from
   reference_order = models.ForeignKey('self', null=True)
   cryptocurrency = models.ForeignKey('Cryptocurrency')

   # bill no of the payment. purchase order only,
   payment_bill_no = models.CharField(max_length=128, null=True)

   # status of the payment, this provides refined status info
   # purchase order only,
   payment_status = models.CharField(max_length=64, choices=PAYMENT_STATUS)

   #reference_wallet = models.ForeignKey('Wallet', null= True)
   # For purchase order only, once unit is delivered, this is the
   # transaction id of
   #reference_wallet_trxId = models.CharField(max_length=128, null = True)
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
   created_by = models.ForeignKey(User, related_name='Order_created_by')
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.ForeignKey(User, related_name='Order_lastupdated_by')

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
   buy_order = models.ForeignKey('Order', null = True, related_name='trans_buy_order')
   sell_order = models.ForeignKey('Order', null = True, related_name='trans_sell_order')
   axf_txId = models.CharField(max_length=128, null = True)
   fromUser = models.ForeignKey(User, null = True, related_name='trans_fromuser')
   fromUser_paymentmethod = models.ForeignKey('UserPaymentMethod', null = True, related_name='trans_fromuser_paymentmethod')
   toUser = models.ForeignKey(User, null = True, related_name='trans_touser')
   toUser_paymentmethod = models.ForeignKey('UserPaymentMethod', null = True, related_name='trans_touser_paymentmethod')
   reference_trans = models.ForeignKey('Transaction', null = True)
   units = models.FloatField(default=0)
   unit_price = models.FloatField(default=0)
   total = models.FloatField(default=0)
   fees = models.FloatField(default=0)
   status = models.CharField(max_length=32, choices=TRANS_STATUS)
   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.ForeignKey(User, related_name='trans_created_by')
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.ForeignKey(User, related_name='trans_lastupdated_by')


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
   created_by = models.ForeignKey(User, related_name='cron_created_by')
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.ForeignKey(User, related_name='cron_lastupdated_by')
