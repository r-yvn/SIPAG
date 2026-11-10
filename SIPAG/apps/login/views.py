from django.contrib.auth import authenticate, get_user_model, login as auth_login, logout as auth_logout
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie

User = get_user_model()


@never_cache
@ensure_csrf_cookie
def login_view(request):
    # If already logged in, redirect directly to home
    if request.user.is_authenticated:
        return redirect('home')

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


@never_cache
def logout_view(request):
    auth_logout(request)
    return redirect('login')


def csrf_failure_view(request, reason=""):
    """Gracefully handle CSRF failure instead of raw yellow 403 screen"""
    return render(request, 'login/login.html', {
        'error_message': 'Your security session expired or was refreshed. Please log in again.'
    }, status=200)
