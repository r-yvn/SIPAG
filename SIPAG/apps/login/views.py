from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.models import User
from django.shortcuts import redirect, render


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
            return render(request, 'login/login.html', {
                'error_message': 'Incorrect password. Please try again.'
            })

    return render(request, 'login/login.html')