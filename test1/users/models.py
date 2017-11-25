from django.db import models

class PaymentProvider(models.Model):
   name = models.CharField(max_length=32)
   config_json = models.TextField()
   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.IntegerField()
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.IntegerField()

class User(models.Model):
   firstname = models.CharField(max_length=32)
   middle = models.CharField(max_length=32)
   lastname = models.CharField(max_length=32)
   email = models.CharField(max_length=64)
   phone = models.CharField(max_length=32)
   config_json = models.TextField()
   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.IntegerField()
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.IntegerField()

class UserLogin(models.Model):
   userId = models.OneToOneField('User', on_delete = models.CASCADE)
   username = models.CharField(max_length=32, primary_key=True)
   passwd_hash = models.CharField(max_length=64)
   alias = models.CharField(max_length=64)
   config_json = models.CharField(max_length=4096)
   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.IntegerField()
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.IntegerField()

class UserPaymentMethod(models.Model):
   userId = models.ForeignKey('User', on_delete=models.CASCADE)
   providerId = models.ForeignKey('PaymentProvider', on_delete=models.CASCADE)
   account_at_provider= models.CharField(max_length=64)
   provider_qrcode_image = models.ImageField()
   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.IntegerField()
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.IntegerField()


class Cryptocurrency(models.Model):
   currency_code = models.CharField(max_length=16, primary_key=True)
   name = models.CharField(max_length=32)
   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.IntegerField()
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.IntegerField()

class Wallet(models.Model):
   cryptocurrent_code = models.ForeignKey('Cryptocurrency', on_delete=models.CASCADE)
   config_json = models.TextField()
   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.IntegerField()
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.IntegerField()


class UserWallet(models.Model):
   user = models.ForeignKey('User', on_delete=models.CASCADE)
   wallet = models.ForeignKey('Wallet', on_delete=models.CASCADE)
   wallet_addr = models.CharField(max_length=128)
   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.IntegerField()
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.IntegerField()

class UserReview(models.Model):
   target_userId = models.ForeignKey('User', on_delete=models.CASCADE, related_name='target_user')
   review_userId = models.ForeignKey('User', on_delete=models.CASCADE, related_name='review_user')
   score = models.FloatField()
   message = models.TextField()
   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.IntegerField()
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.IntegerField()

class UserStatue(models.Model):
   user = models.ForeignKey('User', on_delete=models.CASCADE)
   avg_score = models.FloatField()
   trans_count = models.IntegerField()
   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.IntegerField()
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.IntegerField()

class Order(models.Model):
   ORDER_TYPE = (('BUY','Buy'),('SELL','Sell'))
   CURRENCY = (('CYN', 'Renminbi'), ('USD', 'US Dollar'))
   user = models.ForeignKey('User', on_delete=models.CASCADE)
   reference_order = models.ForeignKey('self', null=True)
   cryptocurrencyId = models.ForeignKey('Cryptocurrency')
   reference_wallet = models.ForeignKey('Wallet', null= True)
   reference_wallet_trxId = models.CharField(max_length=128, null = True)
   order_type = models.CharField(max_length=8, choices=ORDER_TYPE)
   sub_type = models.CharField(max_length=16, default='')
   units = models.FloatField()
   unit_price = models.FloatField()
   unit_price_currency = models.CharField(max_length = 8, choices=CURRENCY, default='CYN')
   status = models.CharField(max_length=32)
   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.IntegerField()
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.IntegerField()

class OrderChangeLog(models.Model):
   order = models.ForeignKey('Order', on_delete=models.CASCADE)
   action = models.CharField(max_length = 32)
   message = models.CharField(max_length = 255)
   timestamp = models.DateTimeField()

