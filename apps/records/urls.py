from django.urls import path
from . import views

app_name = 'records'

urlpatterns = [
    path('management/', views.admin_management_view, name='admin_management'),
    path('residents/', views.resident_records_view, name='resident_records'),
    path('households/', views.household_records_view, name='household_records'),
]
