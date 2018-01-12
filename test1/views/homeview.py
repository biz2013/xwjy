#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.db.models import Q
from django.shortcuts import render, redirect
from controller.global_constants import *
from django.contrib.auth.decorators import login_required

import logging,json

logger = logging.getLogger("site.homepage")

@login_required
def home(request):
    """Show the home page."""
    logger.info("visit home...")
    if (REQ_KEY_USERNAME not in request.session) or (REQ_KEY_USERID not in request.session):
       return render(request, 'html/index.html', {})
    return redirect('accountinfo')
