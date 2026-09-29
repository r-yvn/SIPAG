from django.urls import path
from . import views

urlpatterns =[path('', views.users_settings_view, name='user_settings'),]