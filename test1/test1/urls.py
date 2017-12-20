"""test1 URL Configuration

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
from django.conf.urls import url
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
import logging
from controller.global_utils import *
from . import app
from views import mysellorder

urlpatterns = [
    url(r'^$', app.home),
    url(r'^registration/$', app.registration),
    url(r'^accounts/login/$', app.login, name='login'),
    url(r'^accounts/accountinfo/$', app.accountinfo, name='accountinfo'),
    url(r'^accounts/external_address/$', app.external_address),
    url(r'^accounts/paymentmethods/$', app.payment_method),
    url(r'^axfund/transfer/$', app.transfer),
    url(r'^mysellorder/$', mysellorder.sell_axfund, name="sellorder"),
    url(r'^mysellorder/confirm_payment/$', app.confirm_payment),
    url(r'^mysellorder/heepay/confirm_payment/$', app.heepay_confirm_payment),
    url(r'^purchase/$', app.show_sell_orders_for_purchase, name='purchase'),
    url(r'^purchase/createorder1/$', app.show_purchase_input),
    url(r'^purchase/createorder2/$', app.create_purchase_order),
]
