"""WalletGui URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.urls import include, re_path, path
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from tradeapi.views import api, heepayview

urlpatterns = [
    re_path(r'^purchasetoken/$', api.purchasetoken, name='purchasetoken'),
    re_path(r'^heepayreply/$', heepayview.handle_notification, name='heepay_notification'),
    re_path(r'^cancelorder/$', api.cancelorder, name='cancelorder'),
    re_path(r'^checkorderstatus/$', api.checkorderstatus, name='checkorderstatus'),
    re_path(r'^selltoken/$', api.selltoken, name='selltoken')
    re_path(r'^register/$', api.register, name='register'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
