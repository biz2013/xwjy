from django.shortcuts import render, redirect

def testpage(request):
    return render(request, 'html/testpage.html')