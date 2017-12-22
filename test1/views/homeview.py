#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.db.models import Q
from django.shortcuts import render, redirect
from controller.global_constants import *

import logging,json

logger = logging.getLogger(__name__)

def home(request):
    """Show the home page."""
    if (REQ_KEY_USERNAME not in request.session) or (REQ_KEY_USERID not in request.session):
       return render(request, 'html/index.html', {})
    return redirect('accountinfo')
