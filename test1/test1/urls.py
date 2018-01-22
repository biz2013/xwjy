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
from controller.global_utils import *
from . import app
from views import mysellorder, homeview, accountinfoview, mypurchaseview
from views import account_cronjob, externaladdrview, paymentmethods
from views import redeemview, heepay_notify_view, transactionview
from django.contrib.auth import views as auth_views

urlpatterns = [
    url(r'^$', homeview.home, name='home'),
    url(r'^admin/', admin.site.urls),
    url(r'^testpage/$', app.testpage),
    url(r'^accounts/accountinfo/$', accountinfoview.accountinfo, name='accountinfo'),
    url(r'^accounts/redeem/$', redeemview.redeem),
    url(r'^accounts/external_address/$', externaladdrview.external_address),
    url(r'^accounts/paymentmethods/$', paymentmethods.payment_method, name='paymentmethods'),
    url(r'^axfund/transfer/$', app.transfer),
    url(r'^mysellorder/$', mysellorder.sell_axfund, name="sellorder"),
    url(r'^mysellorder/cancel$', mysellorder.cancel_sell_order, name="cancelsellorder"),
    url(r'^mysellorder/confirm_payment/$', mysellorder.confirm_payment, name="confirm_payment"),
    url(r'^heepay/confirm_payment/$', heepay_notify_view.heepay_confirm_payment),
    url(r'^purchase/$', mypurchaseview.show_active_sell_orders, name='purchase'),
    url(r'^purchase/createorder1/$', mypurchaseview.show_purchase_input, name="input_purchase"),
    url(r'^purchase/createorder2/$', mypurchaseview.create_purchase_order),
    url(r'^account/cron/update_receive/$', account_cronjob.update_account_with_receiving_fund),
    url(r'^registration/$', app.registration),
    url(r'^accounts/login/$', auth_views.login, name='login'),
    url(r'^accounts/logout/$', auth_views.logout, name='logout'),
    url(r'^transhistory/$', transactionview.listusertransactions, name='mytransactions'),
    url(r'^accounts/password_reset/$', auth_views.password_reset, name='password_reset'),
    url(r'^accounts/password_reset_done/$', auth_views.password_reset_done, name='password_reset_done'),
    url(r'^accounts/password_reset_complete/$', auth_views.password_reset_complete, name='password_reset_complete'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$', auth_views.password_reset_confirm, name='password_reset_confirm'),

    # url(r'^accounts/', include('django.contrib.auth.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
