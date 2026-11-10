from django.contrib.auth import authenticate, get_user_model, login as auth_login, logout as auth_logout
from django.shortcuts import redirect, render

User = get_user_model()


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if not User.objects.filter(username=username).exists():
            return render(request, 'login/login.html', {
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


def logout_view(request):
    auth_logout(request)
    return redirect('login')
