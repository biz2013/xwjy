from django.db import models

class GlobalCounter(models.Model):
    counter = models.IntegerField(default=0)
    lastupdated_at = models.DateTimeField(auto_now=True, null=True)
    lastupdated_by = models.CharField(max_length=32)

class UserLogin(models.Model):
   username = models.CharField(max_length=32, primary_key=True)
   passwd_hash = models.CharField(max_length=64)
   alias = models.CharField(max_length=64, default='')
   config_json = models.CharField(max_length=4096)
   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.ForeignKey('self', on_delete = models.CASCADE, related_name="login_created_by", null = True)
   lastupdated_at = models.DateTimeField(auto_now=True, null=True)
   lastupdated_by = models.ForeignKey('self', on_delete=models.CASCADE, related_name="login_lastupdated_by", null = True)

class PaymentProvider(models.Model):
   code = models.CharField(max_length=32, primary_key=True)
   name = models.CharField(max_length=32)
   config_json = models.TextField()
   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.ForeignKey('UserLogin', related_name='PaymentProvider_created_by')
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.ForeignKey('UserLogin', related_name='PaymentProvider_lastupdated_by')

class User(models.Model):
   login = models.OneToOneField('UserLogin', on_delete= models.CASCADE, null=True)
   firstname = models.CharField(max_length=32)
   middle = models.CharField(max_length=32, default='')
   lastname = models.CharField(max_length=32)
   email = models.CharField(max_length=64)
   phone = models.CharField(max_length=32, default='')
   config_json = models.TextField(default='')
   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.ForeignKey('UserLogin', related_name='User_created_by')
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.ForeignKey('UserLogin', related_name='User_lastupdated_by')

class UserPaymentMethod(models.Model):
   user = models.ForeignKey('User', on_delete=models.CASCADE)
   provider = models.ForeignKey('PaymentProvider', on_delete=models.CASCADE)
   account_at_provider = models.CharField(max_length=64)
   provider_qrcode_image = models.ImageField(upload_to='uploads/')
   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.ForeignKey('UserLogin', related_name='UserPaymentMethod_created_by')
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.ForeignKey('UserLogin', related_name='UserPaymentMethod_lastupdated_by')


class Cryptocurrency(models.Model):
   currency_code = models.CharField(max_length=16, primary_key=True)
   name = models.CharField(max_length=32)
   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.ForeignKey('UserLogin', related_name='Cryptocurrency_created_by')
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.ForeignKey('UserLogin', related_name='Cryptocurrency_lastupdated_by')

class Wallet(models.Model):
   name = models.CharField(max_length=32, unique=True, default='first')
   cryptocurrency = models.ForeignKey('Cryptocurrency', on_delete=models.CASCADE)
   config_json = models.TextField()
   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.ForeignKey('UserLogin', related_name='Wallet_created_by')
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.ForeignKey('UserLogin', related_name='Wallet_lastupdated_by')


class UserWallet(models.Model):
   user = models.ForeignKey('User', on_delete=models.CASCADE)
   wallet = models.ForeignKey('Wallet', on_delete=models.CASCADE)
   wallet_addr = models.CharField(max_length=128)
   balance = models.FloatField(default=0.0)
   available_balance = models.FloatField(default=0.0)
   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.ForeignKey('UserLogin', related_name='UserWallet_created_by')
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.ForeignKey('UserLogin', related_name='UserWallet_lastupdated_by')

class UserExternalWalletAddress(models.Model):
   user = models.ForeignKey('User', on_delete=models.CASCADE)
   cryptocurrency_code = models.ForeignKey('Cryptocurrency', on_delete=models.CASCADE)
   address = models.CharField(max_length=128)
   alias = models.CharField(max_length=32, null=True)
   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.ForeignKey('UserLogin', related_name='UserExternalWalletAddress_created_by')
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.ForeignKey('UserLogin', related_name='UserExternalWalletAddress_lastupdated_by')

class UserReview(models.Model):
   target_userId = models.ForeignKey('User', on_delete=models.CASCADE, related_name='target_user')
   review_userId = models.ForeignKey('User', on_delete=models.CASCADE, related_name='review_user')
   score = models.FloatField()
   message = models.TextField()
   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.ForeignKey('UserLogin', related_name='UserReview_created_by')
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.ForeignKey('UserLogin', related_name='UserReview_lastupdated_by')

class UserStatue(models.Model):
   user = models.ForeignKey('User', on_delete=models.CASCADE)
   avg_score = models.FloatField()
   trans_count = models.IntegerField()
   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.ForeignKey('UserLogin', related_name='UserStatue_created_by')
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.ForeignKey('UserLogin', related_name='UserStatue_lastupdated_by')

class Order(models.Model):
   ORDER_TYPE = (('BUY','Buy'),('SELL','Sell'))
   """
   buy_on_ask and sell_on_bid are for future automatic trading for the games
   """
   SUBORDER_TYPE = (('OPEN','Open'), ('BUY_ON_ASK', 'Buy_on_ask'), ('SELL_ON_BID', 'Sell_on_bid'))
   """
   These are not necessarily final, but I think so far we need these
   """
   ORDER_STATUS = (('OPEN','Open'),('CANCELLED','Cancelled'), ('FILLED','Filled'), ('PARTIALFILLED','PartialFilled'),('LOCKED','Locked'))
   CURRENCY = (('CYN', 'Renminbi'), ('USD', 'US Dollar'))

   order_id = models.CharField(max_length=64, primary_key=True)
   user = models.ForeignKey('User', on_delete=models.CASCADE)
   reference_order = models.ForeignKey('self', null=True)
   cryptocurrency = models.ForeignKey('Cryptocurrency')
   reference_wallet = models.ForeignKey('Wallet', null= True)
   reference_wallet_trxId = models.CharField(max_length=128, null = True)
   order_type = models.CharField(max_length=8, choices=ORDER_TYPE)
   sub_type = models.CharField(max_length=16, default='OPEN', choices=SUBORDER_TYPE)
   units = models.FloatField()
   unit_price = models.FloatField()
   unit_price_currency = models.CharField(max_length = 8, choices=CURRENCY, default='CYN')
   """
   We use lock count to verify whether there's buy order lock on the
   sell order
   """
   lock_count = models.IntegerField(default=0)
   """
   how many units left to be taken, for open purchase only
   """
   units_balance = models.FloatField(default=0.0)
   """
   how many units is avaiable for buy, buyer may lock some units but
   they have not paid, so those units are not available for buy. But
   they are not counte as sold or bought since the transaction is not done
   so units_balance may not reflect them
   """
   units_available_to_trade = models.FloatField(default=0.0)

   # the total amount of original units x unit price, used by
   # purchase order.
   total_amount = models.FloatField(default = 0.0)
   status = models.CharField(max_length=32, choices=ORDER_STATUS)
   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.ForeignKey('UserLogin', related_name='Order_created_by')
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.ForeignKey('UserLogin', related_name='Order_lastupdated_by')

class Transaction(models.Model) :
   TRANS_TYPES= (('BUY_ON_ASK','BUY_ON_ASK'), ('SELL_ON_BID', 'SELL_ON_BID'),
         ('SELLER_TRANSFER_AXFUND','SELLER_TRANSFER_AXFUND'),
         ('USER_WITHDRAW_AXFUND', 'USER_WITHDRAW_AXFUND'),
         ('DEPOSIT_AXFUND', 'DEPOSIT_AXFUND'),
         ('UPDATE_OTHER_TRANS', 'UPDATE_OTHER_TRANS'))
   TRANS_STATUS = (('SUCCEED','SUCCESS'),
         ('FAILED','FAILED'))
   transactionId = models.CharField(primary_key=True, max_length=64)
   transactionType = models.CharField(max_length=64, choices=TRANS_TYPES)
   buy_order = models.ForeignKey('Order', null = True, related_name='trans_buy_order')
   sell_order = models.ForeignKey('Order', null = True, related_name='trans_sell_order')
   axf_txId = models.CharField(max_length=128, null = True)
   fromUser = models.ForeignKey('User', null = True, related_name='trans_fromuser')
   fromUser_paymentmethod = models.ForeignKey('UserPaymentMethod', null = True, related_name='trans_fromuser_paymentmethod')
   toUser = models.ForeignKey('User', null = True, related_name='trans_touser')
   toUser_paymentmethod = models.ForeignKey('UserPaymentMethod', null = True, related_name='trans_touser_paymentmethod')
   reference_trans = models.ForeignKey('Transaction', null = True)
   units = models.FloatField(default=0)
   unit_price = models.FloatField(default=0)
   total = models.FloatField(default=0)
   fees = models.FloatField(default=0)
   status = models.CharField(max_length=32, choices=TRANS_STATUS)
   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.ForeignKey('UserLogin', related_name='trans_created_by')
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.ForeignKey('UserLogin', related_name='trans_lastupdated_by')


class OrderChangeLog(models.Model):
   order = models.ForeignKey('Order', on_delete=models.CASCADE)
   action = models.CharField(max_length = 32)
   message = models.CharField(max_length = 255)
   timestamp = models.DateTimeField()
