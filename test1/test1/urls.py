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
from . import app

urlpatterns = [
    url(r'^$', app.home),
    url(r'^/registration/', app.registration),
    url(r'^/accounts/login/', app.login, name="login")
    url(r'^mysellorder/$', app.mysellorder, name="sellorder"),
    url(r'^purchase/$', app.show_sell_orders_for_purchase),
    url(r'^purchase/createorder1/$', app.show_purchase_input),
]
