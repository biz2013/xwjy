#!/usr/bin/python
# -*- coding: utf-8 -*-
from tradeex.models import *
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def setuptestuser(request):
    return HttpResponse(content='ok')

