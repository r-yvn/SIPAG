from apps.core.models import Barangay
from apps.profiles.models import Profile
from apps.user_settings.models import UserSettings
from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import Admin, Encoder, User


@never_cache
@ensure_csrf_cookie
def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        complete_name = f"{first_name} {last_name}".strip()
        barangay = request.POST.get('barangay', '').strip()
        contact_number = request.POST.get('contact_number', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        # Use email as default username if username field is omitted in UI
        username = request.POST.get('username', '').strip() or email
        type_of_user = request.POST.get('type_of_user') or 'encoder'

        if User.objects.filter(username=username).exists():
            return render(request, 'register/register.html', {
                'error_message': 'An account with this email or username already exists. Please choose a different one or log in.'
            })

        if email and User.objects.filter(email=email).exists():
            return render(request, 'register/register.html', {
                'error_message': 'An account with this email address already exists. Please choose a different one or log in.'
            })

        barangay_obj = None
        if barangay:
            barangay_obj, created = Barangay.objects.get_or_create(
                name=barangay,
                defaults={'city': 'Cebu City', 'province': 'Cebu'}
            )

        # 1. Create the custom User
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            contact_number=contact_number,
            barangay=barangay_obj,
            type_of_user=type_of_user,
        )

        # 2. Create linked Profile and UserSettings records
        Profile.objects.create(
            user=user,
            full_name=complete_name,
            bio='',
            profile_image=''
        )

        UserSettings.objects.create(
            user=user,
            dark_mode=False,
            email_notifications=True
        )

        # 3. Create role subtype association
        if type_of_user == 'admin':
            Admin.objects.create(user=user)
        elif type_of_user == 'encoder':
            pass

        messages.success(request, 'Account registered successfully! Please log in.')
        return redirect('login')

    return render(request, 'register/register.html')
