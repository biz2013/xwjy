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
from django.conf.urls import url, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
import logging
from trading.controller.global_utils import *
from trading.views import mysellorderview, homeview, accountinfoview, mypurchaseview
from trading.views import account_cronjob, externaladdrview, paymentmethodsview
from trading.views import redeemview, heepay_notify_view, transactionview
from trading.views import order_batch_process_view, wallet_address_batch
from trading.views import testpageview, transferview, userregistrationview
from django.contrib.auth import views as auth_views

urlpatterns = [
    url(r'^$', homeview.home, name='home'),
    url(r'^testpage/$', testpageview.testpage),
    url(r'^accounts/accountinfo/$', accountinfoview.accountinfo, name='accountinfo'),
    url(r'^accounts/redeem/$', redeemview.redeem),
    url(r'^accounts/external_address/$', externaladdrview.external_address),
    url(r'^accounts/paymentmethods/$', paymentmethodsview.payment_method, name='paymentmethods'),
    url(r'^axfund/transfer/$', transferview.transfer),
    url(r'^mysellorder/$', mysellorderview.sell_axfund, name="sellorder"),
    url(r'^mysellorder/cancel$', mysellorderview.cancel_sell_order, name="cancelsellorder"),
    url(r'^mysellorder/confirm_payment/$', mysellorderview.confirm_payment, name="confirm_payment"),
    url(r'^heepay/confirm_payment/$', heepay_notify_view.heepay_confirm_payment),
    url(r'^purchase/$', mypurchaseview.show_active_sell_orders, name='purchase'),
    url(r'^purchase/createorder1/$', mypurchaseview.show_purchase_input, name="input_purchase"),
    url(r'^purchase/createorder2/$', mypurchaseview.create_purchase_order),
    url(r'^account/cron/update_receive/$', account_cronjob.update_account_with_receiving_fund),
    url(r'^account/cron/order_batch_process/$', order_batch_process_view.order_batch_process),
    url(r'^account/cron/generate_address/$', wallet_address_batch.create_wallet_address),
    url(r'^registration/$', userregistrationview.registration),
    url(r'^transhistory/$', transactionview.listusertransactions, name='mytransactions'),
    url(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', userregistrationview.activate_user_registration, name='activate_user_registration'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
