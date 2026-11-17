from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from .models import UserSettings


@login_required
def users_settings_view(request):
    user = request.user
    settings_obj, _ = UserSettings.objects.get_or_create(user=user)
    profile = getattr(user, 'profile', None)

    if request.method == 'POST':
        dark_mode = request.POST.get('dark_mode') == 'on'
        email_notifications = request.POST.get('email_notifications') == 'on'

        settings_obj.dark_mode = dark_mode
        settings_obj.email_notifications = email_notifications
        settings_obj.save()

        messages.success(request, 'Settings saved successfully!')
        return redirect('user_settings')

    return render(request, 'user_settings/user_settings.html', {
        'user_settings': settings_obj,
        'user_profile': user,
        'profile': profile,
    })
