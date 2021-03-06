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
from walletgui.views import dashboard, paymentmethodview, purchaseview, redeemview
from walletgui.views import transferview, transhistoryview, backupwalletview, apiuser
from walletgui.admin import usermanager

urlpatterns = [
    re_path(r'^$', dashboard.show, name='balance'),
    re_path(r'^paymentmethod/delete', paymentmethodview.delete, name="delete_payment_method"),
    re_path(r'^paymentmethod/create', paymentmethodview.create, name="create_payment_method"),
    re_path(r'^paymentmethod/edit', paymentmethodview.create, name="edit_payment_method"),
    re_path(r'^setup_staking_user/$', usermanager.create, name='create_api_user'),
    re_path(r'^showpurchase/$', purchaseview.show, name='show_purchase'),
    re_path(r'^purchase/$', purchaseview.purchase, name='purchase'),
    re_path(r'^showredeem/$', redeemview.show, name='show_redeem'),
    re_path(r'^showredeem/$', redeemview.redeem, name='redeem'),
    re_path(r'^transfer/$', transferview.show, name='show_transfer'),
    re_path(r'^transhistory/$', transhistoryview.show, name='show_transhistory'),
    re_path(r'^backup/$', backupwalletview.show, name='backupwallet'),
    re_path(r'^apiregister/$', apiuser.register, name='apiregister'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
