from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from .models import User
from apps.profiles.models import Profile
from apps.user_settings.models import UserSettings

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        complete_name = request.POST.get('complete_name')
        contact_number = request.POST.get('contact_number')
        barangay = request.POST.get('barangay')
        type_of_user = request.POST.get('type_of_user')

        if User.objects.filter(username=username).exists():
            return render(request, 'register/register.html', {
                'error_message': 'Username already exists. Please choose a different username.'
            })
        
        user = User.objects.create_user(
            username=username,
            password=password
        )

        profile = Profile(
            user=user, 
            full_name=complete_name, 
            bio='', 
            profile_image=''  
        )

        settings = UserSettings(
            user=user,
            dark_mode=False,
            email_notifications=True
        )

        user_profile = User(
            user=user, 
            barangay=barangay, 
            type_of_user=type_of_user, 
            complete_name=complete_name, 
            contact_number=contact_number
        )
        
        user_profile.save()
        profile.save()
        settings.save()
        return redirect('login')
    return render(request, 'register/register.html')

