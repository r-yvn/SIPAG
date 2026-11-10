from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def resident_records_view(request):
    return render(request, 'home/home.html')


@login_required
def household_records_view(request):
    return render(request, 'home/home.html')
