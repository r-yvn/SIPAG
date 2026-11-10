from apps.core.models import Barangay
from apps.profiles.models import Profile
from apps.user_settings.models import UserSettings
from django.contrib.auth import authenticate, login as auth_login
from django.shortcuts import redirect, render
from .models import Admin, Encoder, User

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        complete_name = f"{first_name} {last_name}".strip()
        contact_number = request.POST.get('contact_number')
        barangay = request.POST.get('barangay')
        type_of_user = request.POST.get('type_of_user')
    
        if User.objects.filter(username=username).exists():
            return render(request, 'register/register.html', {
                'error_message': 'Username already exists. Please choose a different username.'
            })

        barangay_obj = None
        if barangay:
            barangay_obj, created = Barangay.objects.get_or_create(
                name=barangay.strip(),
                defaults={'city': '', 'province': ''}
            )

        # 2. Create the custom User with all fields populated properly
        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            contact_number=contact_number,
            barangay=barangay_obj,  # <--- Passing the actual Barangay object, not a string
            type_of_user=type_of_user,
        )

        # 3. Create linked Profile and UserSettings records
        Profile.objects.create(
            user=user, full_name=complete_name, bio='', profile_image=''
        )

        UserSettings.objects.create(
            user=user, dark_mode=False, email_notifications=True
        )

        # 4. Create subtype association based on role
        if type_of_user == 'admin':
            Admin.objects.create(user=user)
        elif type_of_user == 'encoder':
            # Note: Encoders can be assigned a sitio later by the admin, 
            # or you can assign a default sitio if required by your schema.
            pass

        return redirect('login')

    return render(request, 'register/register.html')