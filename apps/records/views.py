from datetime import date
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from apps.core.models import Sitio
from apps.records.models import HouseholdRecord, ResidentRecord

User = get_user_model()


@login_required
def admin_management_view(request):
    is_admin = getattr(request.user, 'type_of_user', '') == 'admin' or request.user.is_staff or request.user.is_superuser
    if not is_admin:
        messages.error(request, "Access restricted to administrators.")
        return redirect('home')

    # Handle management actions
    if request.method == 'POST':
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')
        if action and user_id:
            target_user = get_object_or_404(User, pk=user_id)
            if action == 'accept':
                target_user.is_active = True
                target_user.save()
                messages.success(request, f"Encoder {target_user.get_full_name() or target_user.username} has been approved.")
            elif action == 'decline':
                target_user.delete()
                messages.info(request, "Encoder request declined.")
            elif action == 'deactivate':
                target_user.is_active = False
                target_user.save()
                messages.warning(request, f"User {target_user.username} deactivated.")
            elif action == 'suspend':
                target_user.is_active = False
                target_user.save()
                messages.warning(request, f"User {target_user.username} suspended.")
        return redirect('records:admin_management')

    pending_encoders = User.objects.filter(type_of_user='encoder', is_active=False).order_by('-date_joined')
    active_users = User.objects.filter(is_active=True).order_by('-date_joined')

    context = {
        'pending_encoders': pending_encoders,
        'active_users': active_users,
        'is_admin': is_admin,
    }
    return render(request, 'records/admin_management.html', context)


@login_required
def resident_records_view(request):
    is_admin = getattr(request.user, 'type_of_user', '') == 'admin' or request.user.is_staff or request.user.is_superuser

    if request.method == 'POST':
        # Add new resident
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        middle_name = request.POST.get('middle_name', '').strip()
        suffix_name = request.POST.get('suffix_name', '').strip()
        sex = request.POST.get('sex', 'male').lower()
        date_of_birth = request.POST.get('date_of_birth')
        place_of_birth = request.POST.get('place_of_birth', '').strip() or 'Cebu City'
        civil_status = request.POST.get('civil_status', 'single').lower()
        occupation = request.POST.get('occupation', '').strip()
        contact_number = request.POST.get('contact_number', '').strip()
        household_id = request.POST.get('household_id')

        household_obj = None
        if household_id:
            household_obj = HouseholdRecord.objects.filter(pk=household_id).first()

        if first_name and last_name and date_of_birth:
            ResidentRecord.objects.create(
                first_name=first_name,
                last_name=last_name,
                middle_name=middle_name,
                suffix_name=suffix_name,
                sex=sex,
                date_of_birth=date_of_birth,
                place_of_birth=place_of_birth,
                civil_status=civil_status,
                occupation=occupation,
                contact_number=contact_number,
                household=household_obj,
                created_by=request.user,
                encoder=request.user,
                status='active'
            )
            messages.success(request, f"Resident {first_name} {last_name} created successfully.")
            return redirect('records:resident_records')

    q = request.GET.get('q', '').strip()
    residents_qs = ResidentRecord.objects.select_related('household', 'household__sitio').all()
    if q:
        residents_qs = residents_qs.filter(
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(household__street__icontains=q) |
            Q(household__sitio__name__icontains=q)
        )
    residents_qs = residents_qs.order_by('-created_at')

    sitios = Sitio.objects.all().order_by('name')
    households = HouseholdRecord.objects.select_related('sitio').all().order_by('house_number')

    context = {
        'residents': residents_qs,
        'sitios': sitios,
        'households': households,
        'q': q,
        'is_admin': is_admin,
    }
    return render(request, 'records/resident_records.html', context)


@login_required
def household_records_view(request):
    is_admin = getattr(request.user, 'type_of_user', '') == 'admin' or request.user.is_staff or request.user.is_superuser

    if request.method == 'POST':
        # Add new household
        house_number = request.POST.get('house_number', '').strip()
        street = request.POST.get('street', '').strip()
        sitio_id = request.POST.get('sitio_id')

        sitio_obj = None
        if sitio_id:
            sitio_obj = Sitio.objects.filter(pk=sitio_id).first()
        else:
            sitio_obj = Sitio.objects.first()

        if house_number and sitio_obj:
            HouseholdRecord.objects.create(
                house_number=house_number,
                street=street,
                sitio=sitio_obj,
                created_by=request.user,
            )
            messages.success(request, f"Household #{house_number} created successfully.")
            return redirect('records:household_records')

    q = request.GET.get('q', '').strip()
    households_qs = HouseholdRecord.objects.select_related('sitio', 'head_of_household').all()
    if q:
        households_qs = households_qs.filter(
            Q(house_number__icontains=q) |
            Q(street__icontains=q) |
            Q(sitio__name__icontains=q)
        )
    households_qs = households_qs.annotate(total_members=Count('household')).order_by('-created_at')

    sitios = Sitio.objects.all().order_by('name')

    context = {
        'households': households_qs,
        'sitios': sitios,
        'q': q,
        'is_admin': is_admin,
    }
    return render(request, 'records/household_records.html', context)
