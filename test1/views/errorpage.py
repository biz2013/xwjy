#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.db.models import Q
from django.shortcuts import render, redirect

def show_error(request, error_level, error_msg):
    return render(request, 'html/error_page.html',
                  { 'error_level' : error_level,
                    'error_msg': error_msg})
