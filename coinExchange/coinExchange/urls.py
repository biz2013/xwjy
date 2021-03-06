"""coinExchange URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, re_path, path
from django.conf import settings
from django.contrib.auth import views as auth_views
from django.conf.urls.static import static
from testsetup import setuptest

urlpatterns = [
    re_path(r'^trading/', include('trading.urls')),
    re_path(r'^api/v1/', include('tradeex.urls')),
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^accounts/', include('django.contrib.auth.urls')),
    re_path(r'^setuptest/$', setuptest.setuptestuser),
    re_path(r'^setup_fix/$', setuptest.fix),
    re_path(r'^setup_create_api_user/$', setuptest.create_api_user),
    re_path(r'^trigger_purchase_notify/$', setuptest.send_notify_test),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

#Add URL maps to redirect the base URL to our application
from django.views.generic import RedirectView
urlpatterns += [
    path('', RedirectView.as_view(url='/trading/', permanent=True)),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
