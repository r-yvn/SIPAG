from django.urls import path
from . import views

app_name = 'records'

urlpatterns = [
    path('management/', views.admin_management_view, name='admin_management'),
    path('residents/', views.resident_records_view, name='resident_records'),
    path('households/', views.household_records_view, name='household_records'),
    path('api/search-households/', views.search_households_api, name='search_households_api'),
    path('api/search-residents/', views.search_residents_api, name='search_residents_api'),
]