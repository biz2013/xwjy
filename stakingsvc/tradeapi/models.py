from django.db import models
from django.contrib.auth.models import User

# user profile for API User
class UserProfile(models.Model):
   USER_TYPE = (('TRADEUSER', 'TradeUser'), 'APIUSER', 'APIUser')
   user = models.ForeignKey(User, on_delete=models.CASCADE)
   user_type = models.CharField(max_length=32, choices=USER_TYPE, default='APIUSER')
   api_key = models.CharField(max_length=128, default='')
   api_secret = models.CharField(max_length=128, default='')

   created_at = models.DateTimeField(auto_now_add=True)
   created_by = models.ForeignKey(User, related_name='UserProfile_created_by', on_delete=models.SET_NULL, null=True)
   lastupdated_at = models.DateTimeField(auto_now=True)
   lastupdated_by = models.ForeignKey(User, related_name='UserProfile_lastupdated_by', on_delete=models.SET_NULL, null=True)

