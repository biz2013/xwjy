from django.shortcuts import render

def home(request):
    """Show the home page."""
    return render(request, 'html/index.html')

def mysellorder(request):
    return render(request, 'html/mysellorder.html')
