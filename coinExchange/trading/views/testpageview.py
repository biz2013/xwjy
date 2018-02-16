from django.shortcuts import render, redirect

def testpage(request):
    return render(request, 'trading/testpage.html')