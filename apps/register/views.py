from apps.core.models import Barangay
from apps.profiles.models import Profile
from apps.user_settings.models import UserSettings
from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import Encoder, User


@never_cache
@ensure_csrf_cookie
def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        complete_name = f"{first_name} {last_name}".strip()
        barangay_name = request.POST.get('barangay', '').strip()
        contact_number = request.POST.get('contact_number', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        username = request.POST.get('username', '').strip() or email

        if not (first_name and last_name and barangay_name and email and password):
            return render(request, 'register/register.html', {
                'error_message': 'Please fill out all required fields.'
            })

        if User.objects.filter(username__iexact=username).exists() or User.objects.filter(email__iexact=email).exists():
            return render(request, 'register/register.html', {
                'error_message': 'An account with this email or username already exists. Please choose another or log in.'
            })

        barangay_obj = Barangay.objects.filter(name__iexact=barangay_name).first()
        if not barangay_obj:
            barangay_obj = Barangay.objects.create(
                name=barangay_name,
                city='Cebu City',
                province='Cebu'
            )

        # Always register as an Encoder awaiting Admin approval & Sitio assignment
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            contact_number=contact_number,
            barangay=barangay_obj,
            type_of_user='encoder',
            account_status='pending',
            is_active=False,
        )

        # Create Encoder row with sitio=None for the Admin Management inner join
        Encoder.objects.create(user=user, sitio=None)

        Profile.objects.create(
            user=user,
            full_name=complete_name,
            bio='',
            profile_image=''
        )

        UserSettings.objects.create(
            user=user,
            dark_mode=False,
            skin='default',
            email_notifications=True
        )

        messages.success(
            request,
            'Account registered! Please wait for your Barangay Admin to approve your account and assign your Sitio.'
        )
        return redirect('login')

    return render(request, 'register/register.html')