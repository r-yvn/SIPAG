from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from apps.profiles.models import Profile
from apps.user_settings.models import UserSettings


@login_required
def profile_view(request):
    user = request.user
    profile, _ = Profile.objects.get_or_create(
        user=user,
        defaults={
            'full_name': f"{user.first_name} {user.last_name}".strip(),
            'bio': '',
        }
    )
    settings_obj, _ = UserSettings.objects.get_or_create(user=user)

    if request.method == 'POST':
        bio = request.POST.get('bio', '')
        profile.bio = bio
        profile.save()
        return redirect('profile')

    return render(request, 'profiles/profile.html', {
        'user_profile': user,
        'profile': profile,
        'user_skin': settings_obj.skin or ('dark' if settings_obj.dark_mode else 'default'),
    })