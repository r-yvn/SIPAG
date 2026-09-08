from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from .models import UserProfile

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        complete_name = request.POST.get('complete_name')
        contact_number = request.POST.get('contact_number')
        barangay = request.POST.get('barangay')
        type_of_user = request.POST.get('type_of_user')

        user = User.objects.create_user(
            username=username,
            password=password
        )


        user_profile = UserProfile(user=user, barangay=barangay, type_of_user=type_of_user, complete_name=complete_name, contact_number=contact_number)
        user_profile.save()
        return redirect('login')
    return render(request, 'accounts/register.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not User.objects.filter(username=username).exists():
            return render(request, 'accounts/login.html', {
                'error_message': 'User does not exist. Please register an account first.'
            })

        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)
            return redirect('home')
        else:
            return render(request, 'accounts/login.html', {
                'error_message': 'Incorrect password. Please try again.'
            })

    return render(request, 'accounts/login.html')