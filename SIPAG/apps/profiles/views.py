from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from apps.profiles.models import Profile


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
    if request.method == 'POST':
        bio = request.POST.get('bio', '')
        profile.bio = bio
        profile.save()
        return redirect('profile')

    return render(request, 'profiles/profile.html', {
        'user_profile': user,
        'profile': profile,
    })
