#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.contrib.auth import logout
from walletgui.controller.global_constants import *

def show_error(request, error_level, error_msg):
    if error_level == ERR_CRITICAL_IRRECOVERABLE:
        logout(request)
    return render(request, 'walletgui/error_page.html', { 'error_msg': error_msg})
