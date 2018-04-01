from django.shortcuts import render


def landing(request):
    return render(request, 'call_your_mom/landing.html')
