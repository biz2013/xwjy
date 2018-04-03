from django.db import models
from django.contrib.auth.models import User
from trading.models import Cryptocurrency

# Create your models here.

class APIUserAccount(models.Model):
   ACCOUNT_STATUS =(('OPEN', 'Open'),
        ('ACTIVE', 'Active'),
        ('PENDING', 'Pending'),
        ('SUSPENDED', 'Suspended'),
        ('CLOSED', 'Closed'))
   user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
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
