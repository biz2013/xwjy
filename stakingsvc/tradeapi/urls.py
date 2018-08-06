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
from tradeapi.views import prepurchaseview, apirelay

urlpatterns = [
    re_path(r'^applypurchase/$', apirelay.purchase, name='prepurchase'),
    re_path(r'^applyredeem/$', apirelay.redeem, name='redeem'),
    re_path(r'^checkstatus/$', apirelay.checkstatus, name='checkstatus'),
    re_path(r'^closetransaction/$', apirelay.closetransaction, name='closetransaction'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
