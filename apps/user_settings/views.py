from django.contrib import messages
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from apps.profiles.models import Profile
from .models import UserSettings

User = get_user_model()

@login_required
def users_settings_view(request):
    user = request.user
    settings_obj, _ = UserSettings.objects.get_or_create(user=user)
    is_admin = getattr(user, 'type_of_user', '') == 'admin' or user.is_staff or user.is_superuser
    active_tab = request.GET.get('tab', 'details')

    if request.method == 'POST':
        tab = request.POST.get('tab', 'details')
        active_tab = tab

        if tab == 'details':
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            email = request.POST.get('email', '').strip().lower()
            contact_number = request.POST.get('contact_number', '').strip()

            if email and User.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
                messages.error(request, 'That email address is already in use by another account.')
                return redirect(f"{request.path}?tab=details")

            if first_name:
                user.first_name = first_name
            if last_name:
                user.last_name = last_name
            if email:
                user.email = email
            if hasattr(user, 'contact_number'):
                user.contact_number = contact_number
            user.save()

            profile = Profile.objects.filter(user=user).first()
            if profile:
                profile.full_name = f"{user.first_name} {user.last_name}".strip()
                profile.save()

            messages.success(request, 'Profile details updated successfully!')

        elif tab == 'password':
            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')
            if new_password and new_password == confirm_password:
                user.set_password(new_password)
                user.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password changed successfully!')
            elif new_password != confirm_password:
                messages.error(request, 'Passwords do not match.')
            else:
                messages.error(request, 'Please enter a valid password.')

        elif tab == 'preference':
            email_notifications = request.POST.get('email_notifications') == 'on'
            skin = request.POST.get('skin', 'default')
            if skin not in ('default', 'light', 'dark'):
                skin = 'default'

            settings_obj.email_notifications = email_notifications
            settings_obj.skin = skin
            settings_obj.dark_mode = (skin == 'dark')
            settings_obj.save()
            messages.success(request, 'Preferences saved successfully!')

        return redirect(f"{request.path}?tab={active_tab}")

    return render(request, 'user_settings/user_settings.html', {
        'user_settings': settings_obj,
        'user_profile': user,
        'is_admin': is_admin,
        'active_tab': active_tab,
        'user_skin': settings_obj.skin or ('dark' if settings_obj.dark_mode else 'default'),
    })