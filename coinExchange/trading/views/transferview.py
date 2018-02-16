
from django.shortcuts import render, redirect

def transfer(request):
    return render(request, 'trading/myaccount.html')