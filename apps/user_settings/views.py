from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from .models import UserSettings


@login_required
def users_settings_view(request):
    user = request.user
    settings_obj, _ = UserSettings.objects.get_or_create(user=user)
    is_admin = getattr(user, 'type_of_user', '') == 'admin' or user.is_staff or user.is_superuser

    if request.method == 'POST':
        tab = request.POST.get('tab', 'details')

        if tab == 'details':
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            email = request.POST.get('email', '').strip()
            contact_number = request.POST.get('contact_number', '').strip()

            if first_name:
                user.first_name = first_name
            if last_name:
                user.last_name = last_name
            if email:
                user.email = email
            if contact_number and hasattr(user, 'contact_number'):
                user.contact_number = contact_number
            user.save()
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
            settings_obj.email_notifications = email_notifications
            settings_obj.save()
            messages.success(request, 'Preferences saved successfully!')

        return redirect('user_settings')

    return render(request, 'user_settings/user_settings.html', {
        'user_settings': settings_obj,
        'user_profile': user,
        'is_admin': is_admin,
    })
