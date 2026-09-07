from django.shortcuts import render
from .models import Resident

def home(request):
    profile = request.user.profile
    residents = Resident.objects.filter(status="active")
    display = {
        'complete_name' : profile.complete_name,
        'type_of_user' : profile.type_of_user,  
        'username' : request.user.username,
        'residents' : residents
    }
    return render(request, 'residents/home.html', display)