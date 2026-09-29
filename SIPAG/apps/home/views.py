from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Home

@login_required
def home_view(request):
    return render(request, 'home/home.html')