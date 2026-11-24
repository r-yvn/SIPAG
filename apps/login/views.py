from django.contrib.auth import authenticate, get_user_model, login as auth_login, logout as auth_logout
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie

User = get_user_model()


@never_cache
@ensure_csrf_cookie
def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        login_id = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user_obj = User.objects.filter(username=login_id).first()
        if not user_obj:
            user_obj = User.objects.filter(email__iexact=login_id).first()

        if not user_obj:
            return render(request, 'login/login.html', {
                'error_message': 'User does not exist. Please register an account first.'
            })

        if not user_obj.is_active:
            status = getattr(user_obj, 'account_status', 'pending')
            if status == 'pending':
                msg = 'Your account is pending Barangay Admin approval and Sitio assignment.'
            elif status == 'suspended':
                msg = 'Your account has been suspended. Please contact your Barangay Admin.'
            else:
                msg = 'Your account is currently deactivated. Please contact your Barangay Admin.'
            return render(request, 'login/login.html', {'error_message': msg})

        user = authenticate(request, username=user_obj.username, password=password)

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


def forgot_password_view(request):
    submitted = False
    if request.method == 'POST':
        submitted = True
    return render(request, 'login/forgot_password.html', {'submitted': submitted})


def csrf_failure_view(request, reason=""):
    return render(request, 'login/login.html', {
        'error_message': 'Your security session expired or was refreshed. Please log in again.'
    }, status=200)