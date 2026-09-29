from django.shortcuts import render
from apps.register.models import UserProfile
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.models import User

def profile_view(request):
    user_profile = get_object_or_404(UserProfile, user=request.user)
    return render(request, 'profiles/profile.html', {'user_profile' : user_profile})
