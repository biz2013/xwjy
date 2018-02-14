#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.db.models import Q
from django.shortcuts import render, redirect
from trading.controller.global_constants import *

def show_error(request, error_level, error_msg):
    if error_level == ERR_CRITICAL_IRRECOVERABLE:
        request.session[REQ_KEY_USERNAME] = None
        request.session[REQ_KEY_USERID] = None
    return render(request, 'html/error_page.html', { 'error_msg': error_msg})
