#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.db.models import Q
from django.shortcuts import render, redirect
from controller.global_constants import *

import logging,json

logger = logging.getLogger(__name__)

def home(request):
    """Show the home page."""
    if REQ_KEY_USERNAME in request.session:
       return redirect('accountinfo')
    return render(request, 'html/index.html', {})
