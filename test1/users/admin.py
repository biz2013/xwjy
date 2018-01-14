from django.contrib import admin
from .models import SiteSettings, Transaction

admin.site.register(SiteSettings)
admin.site.register(Transaction)
