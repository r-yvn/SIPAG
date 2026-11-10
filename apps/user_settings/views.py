from django.shortcuts import render

def users_settings_view(request):
    
    return render(request, 'user_settings/user_settings.html')
