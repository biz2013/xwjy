from django.db import models

class User(models.Model):
   username = models.CharField(max_length=32, primary_key=True)
   passwd = models.CharField(max_length=32)
   email = models.CharField(max_length=128)

class Currency(models.Model):
   currency_code = models.CharField(max_length=8, primary_key=True)
   currency = models.CharField(max_length=32)

class CryptoAccount(models.Model):
   username = models.ForeignKey('User')
   account = models.CharField(max_length=128)
   balance = models.FloatField()
   
class PaymentProvider(models.Model):
   provider = models.CharField(max_length=32, primary_key=True)
   config = models.CharField(max_length=256)

class ExternalPaymentMethod(models.Model):
   username = models.ForeignKey('User')
   provider = models.ForeignKey('PaymentProvider')
   accountNo = models.CharField(max_length=32)
   acct_qrcode_image = models.ImageField()

class Order(models.Model):
   username = models.ForeignKey('User')
   order_type = models.CharField(max_length=8)
   account = models.ForeignKey('CryptoAccount')
   amount = models.FloatField()
   created_at = models.DateTimeField()
   status = models.CharField(max_length=16)
