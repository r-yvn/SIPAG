from datetime import date
from urllib.parse import urlencode
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q, Subquery
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from apps.core.models import Barangay, Sitio
from apps.records.models import ActivityLog, HouseholdRecord, ResidentRecord
from apps.register.models import Admin, Encoder
from apps.user_settings.models import UserSettings

User = get_user_model()


def _subtract_years(d, years):
    try:
        return d.replace(year=d.year - years)
    except ValueError:
        return d.replace(month=2, day=28, year=d.year - years)


def _get_scope(user):
    is_admin = getattr(user, 'type_of_user', '') == 'admin' or user.is_staff or user.is_superuser
    if is_admin:
        return True, user.barangay, None
    encoder_obj = Encoder.objects.filter(user=user).select_related('sitio').first()
    assigned_sitio = encoder_obj.sitio if encoder_obj else None
    return False, user.barangay, assigned_sitio


def _get_user_skin(user):
    settings_obj, _ = UserSettings.objects.get_or_create(user=user)
    return settings_obj.skin or ('dark' if settings_obj.dark_mode else 'default')


def _log_activity(actor, action_type, action_performed, sitio=None, barangay=None):
    role = 'Admin' if (getattr(actor, 'type_of_user', '') == 'admin' or actor.is_staff or actor.is_superuser) else 'Encoder'
    resolved_barangay = barangay or (sitio.barangay if sitio else None) or actor.barangay
    ActivityLog.objects.create(
        barangay=resolved_barangay,
        sitio=sitio,
        user=actor,
        user_name=actor.get_full_name() or actor.username,
        role=role,
        action_type=action_type,
        action_performed=action_performed,
    )


@login_required
def admin_management_view(request):
    is_admin, barangay, _ = _get_scope(request.user)
    if not is_admin:
        messages.error(request, "Access restricted to administrators.")
        return redirect('home')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_sitio':
            sitio_name = request.POST.get('sitio_name', '').strip()
            target_barangay = barangay or Barangay.objects.first()
            if sitio_name and target_barangay:
                sitio_obj, created = Sitio.objects.get_or_create(name=sitio_name, barangay=target_barangay)
                if created:
                    _log_activity(request.user, 'add_sitio', f"Added Sitio: {sitio_obj.name}", sitio=sitio_obj, barangay=target_barangay)
                messages.success(request, f"Sitio '{sitio_name}' added.")
            else:
                messages.error(request, "Please provide a valid Sitio name and Barangay.")
            return redirect('records:admin_management')

        user_id = request.POST.get('user_id')
        if action and user_id:
            target_user = get_object_or_404(User, pk=user_id)

            if action == 'accept':
                sitio_id = request.POST.get('sitio_id')
                sitio_obj = Sitio.objects.filter(pk=sitio_id).first() if sitio_id else None
                if not sitio_obj:
                    messages.error(request, "Please select a Sitio before accepting an encoder.")
                    return redirect('records:admin_management')

                target_user.is_active = True
                target_user.account_status = 'active'
                target_user.type_of_user = 'encoder'
                target_user.save()

                Encoder.objects.update_or_create(user=target_user, defaults={'sitio': sitio_obj})
                _log_activity(
                    request.user,
                    'approve_encoder',
                    f"Approved Encoder: {target_user.get_full_name() or target_user.username}",
                    sitio=sitio_obj,
                    barangay=target_user.barangay,
                )
                messages.success(
                    request,
                    f"Encoder {target_user.get_full_name() or target_user.username} approved and assigned to {sitio_obj.name}."
                )

            elif action == 'decline':
                declined_name = target_user.get_full_name() or target_user.username
                declined_barangay = target_user.barangay
                target_user.delete()
                _log_activity(
                    request.user,
                    'decline_encoder',
                    f"Declined Encoder: {declined_name}",
                    barangay=declined_barangay,
                )
                messages.info(request, "Pending encoder request declined and removed.")

            elif action == 'manage_user':
                new_role = request.POST.get('role', target_user.type_of_user)
                new_status = request.POST.get('account_status', target_user.account_status)
                sitio_id = request.POST.get('sitio_id')

                if target_user.pk == request.user.pk and new_status != 'active':
                    messages.error(request, "You cannot deactivate or suspend your own currently logged-in account.")
                    return redirect('records:admin_management')

                if target_user.pk == request.user.pk and new_role != 'admin':
                    messages.error(request, "You cannot demote your own currently logged-in admin account.")
                    return redirect('records:admin_management')

                assigned_sitio_obj = None
                if new_role == 'encoder':
                    assigned_sitio_obj = Sitio.objects.filter(pk=sitio_id).first() if sitio_id else None
                    if not assigned_sitio_obj:
                        messages.error(request, "Encoders must be assigned to a Sitio.")
                        return redirect('records:admin_management')
                    target_user.type_of_user = 'encoder'
                    Admin.objects.filter(user=target_user).delete()
                    Encoder.objects.update_or_create(user=target_user, defaults={'sitio': assigned_sitio_obj})
                else:
                    target_user.type_of_user = 'admin'
                    Encoder.objects.filter(user=target_user).delete()
                    Admin.objects.get_or_create(user=target_user)

                target_user.account_status = new_status
                target_user.is_active = (new_status == 'active')
                target_user.save()

                _log_activity(
                    request.user,
                    'manage_user',
                    f"Updated User ({target_user.type_of_user.title()}, {new_status.title()}): {target_user.get_full_name() or target_user.username}",
                    sitio=assigned_sitio_obj,
                    barangay=target_user.barangay,
                )
                messages.success(request, f"Updated user {target_user.get_full_name() or target_user.username}.")

        return redirect('records:admin_management')

    # Pending Encoders (INNER JOIN between encoder and user)
    pending_qs = Encoder.objects.select_related('user', 'user__barangay', 'sitio').filter(
        user__type_of_user='encoder',
        user__account_status='pending',
    )
    users_qs = User.objects.exclude(account_status='pending').select_related('barangay').prefetch_related('encoders__sitio')
    sitios_qs = Sitio.objects.all()

    if barangay:
        pending_qs = pending_qs.filter(user__barangay=barangay)
        users_qs = users_qs.filter(barangay=barangay)
        sitios_qs = sitios_qs.filter(barangay=barangay)

    pending_qs = pending_qs.order_by('-user__date_joined')
    users_qs = users_qs.order_by('-date_joined')
    sitios = sitios_qs.order_by('name')

    # Separate paginators for the two tables
    pending_paginator = Paginator(pending_qs, 5)
    pending_page = pending_paginator.get_page(request.GET.get('pending_page'))
    pending_elided_range = pending_paginator.get_elided_page_range(pending_page.number, on_each_side=1, on_ends=1)

    users_paginator = Paginator(users_qs, 8)
    users_page = users_paginator.get_page(request.GET.get('users_page'))
    users_elided_range = users_paginator.get_elided_page_range(users_page.number, on_each_side=1, on_ends=1)

    for u in users_page:
        enc = u.encoders.first()
        u.assigned_sitio_id = enc.sitio_id if enc else ''
        u.assigned_sitio_name = enc.sitio.name if (enc and enc.sitio) else 'All (Barangay)'

    return render(request, 'records/admin_management.html', {
        'pending_encoders': pending_page,
        'pending_elided_range': pending_elided_range,
        'pending_extra_query': urlencode({'users_page': users_page.number}),
        'managed_users': users_page,
        'users_elided_range': users_elided_range,
        'users_extra_query': urlencode({'pending_page': pending_page.number}),
        'sitios': sitios,
        'is_admin': is_admin,
        'user_skin': _get_user_skin(request.user),
    })


@login_required
def resident_records_view(request):
    is_admin, barangay, assigned_sitio = _get_scope(request.user)

    if not is_admin and not assigned_sitio:
        messages.warning(request, "You have not been assigned to a Sitio yet. Please contact your Barangay Admin.")

    if request.method == 'POST':
        action = request.POST.get('action', 'create')
        resident_id = request.POST.get('resident_id')

        first_name = request.POST.get('first_name', '').strip()
        middle_name = request.POST.get('middle_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        suffix_name = request.POST.get('suffix_name', '').strip()
        sex = request.POST.get('sex', 'male').lower()
        date_of_birth = request.POST.get('date_of_birth')
        place_of_birth = request.POST.get('place_of_birth', '').strip() or 'Cebu City'
        civil_status = request.POST.get('civil_status', 'single').lower()
        voter_status = request.POST.get('voter_status', '').strip()
        contact_number = request.POST.get('contact_number', '').strip()
        occupation = request.POST.get('occupation', '').strip()
        address = request.POST.get('address', '').strip()
        household_id = request.POST.get('household_id')
        sitio_id = request.POST.get('sitio_id')
        status = request.POST.get('status', 'active').lower()
        is_pwd = request.POST.get('is_pwd') == 'on'
        is_head = request.POST.get('is_head_of_household') == 'on'

        household_obj = HouseholdRecord.objects.filter(pk=household_id).select_related('sitio').first() if household_id else None

        if household_obj:
            sitio_obj = household_obj.sitio
            if not address:
                address = household_obj.full_address
        elif not is_admin:
            sitio_obj = assigned_sitio
        else:
            sitio_obj = Sitio.objects.filter(pk=sitio_id).first() if sitio_id else None

        if not (first_name and last_name and date_of_birth):
            messages.error(request, "First name, Last name, and Date of Birth are required.")
            return redirect('records:resident_records')

        if action == 'edit' and resident_id:
            resident = get_object_or_404(ResidentRecord, pk=resident_id)
            if not is_admin and resident.sitio != assigned_sitio and (not resident.household or resident.household.sitio != assigned_sitio):
                messages.error(request, "You do not have permission to edit residents outside your assigned Sitio.")
                return redirect('records:resident_records')

            previous_household = resident.household

            resident.first_name = first_name
            resident.middle_name = middle_name
            resident.last_name = last_name
            resident.suffix_name = suffix_name
            resident.sex = sex
            resident.date_of_birth = date_of_birth
            resident.place_of_birth = place_of_birth
            resident.civil_status = civil_status
            resident.voter_status = voter_status
            resident.contact_number = contact_number
            resident.occupation = occupation
            resident.address = address
            resident.household = household_obj
            resident.sitio = sitio_obj
            resident.status = status
            resident.is_pwd = is_pwd
            resident.updated_by = request.user
            resident.save()

            if previous_household and previous_household != household_obj and previous_household.head_of_household_id == resident.resident_id:
                previous_household.head_of_household = None
                previous_household.save()

            _log_activity(
                request.user,
                'edit_resident',
                f"Edited Resident: {first_name} {last_name}",
                sitio=sitio_obj,
                barangay=barangay,
            )
            messages.success(request, f"Resident {first_name} {last_name} updated successfully.")
        else:
            resident = ResidentRecord.objects.create(
                first_name=first_name,
                middle_name=middle_name,
                last_name=last_name,
                suffix_name=suffix_name,
                sex=sex,
                date_of_birth=date_of_birth,
                place_of_birth=place_of_birth,
                civil_status=civil_status,
                occupation=occupation,
                contact_number=contact_number,
                voter_status=voter_status,
                address=address,
                household=household_obj,
                sitio=sitio_obj,
                is_pwd=is_pwd,
                created_by=request.user,
                updated_by=request.user,
                encoder=request.user,
                status=status if status in ('active', 'deceased', 'moved_out') else 'active',
            )
            _log_activity(
                request.user,
                'add_resident',
                f"Added Resident: {first_name} {last_name}",
                sitio=sitio_obj,
                barangay=barangay,
            )
            messages.success(request, f"Resident {first_name} {last_name} created successfully.")

        if household_obj:
            if is_head:
                household_obj.head_of_household = resident
                household_obj.save()
            elif household_obj.head_of_household_id == resident.resident_id:
                household_obj.head_of_household = None
                household_obj.save()

        return redirect('records:resident_records')

    residents_qs = ResidentRecord.objects.select_related('household', 'household__sitio', 'sitio').all()
    sitios_qs = Sitio.objects.all()

    if is_admin:
        if barangay:
            residents_qs = residents_qs.filter(
                Q(household__sitio__barangay=barangay) | Q(sitio__barangay=barangay)
            )
            sitios_qs = sitios_qs.filter(barangay=barangay)
    else:
        if assigned_sitio:
            residents_qs = residents_qs.filter(
                Q(household__sitio=assigned_sitio) | Q(sitio=assigned_sitio)
            )
            sitios_qs = sitios_qs.filter(pk=assigned_sitio.pk)
        else:
            residents_qs = ResidentRecord.objects.none()
            sitios_qs = Sitio.objects.none()

    q = request.GET.get('q', '').strip()
    if q:
        residents_qs = residents_qs.filter(
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(address__icontains=q) |
            Q(household__house_number__icontains=q) |
            Q(household__street__icontains=q) |
            Q(household__sitio__name__icontains=q) |
            Q(sitio__name__icontains=q)
        )

    category = request.GET.get('category', '').strip().lower()
    today = date.today()
    underage_cutoff = _subtract_years(today, 18)
    senior_cutoff = _subtract_years(today, 60)

    if category == 'female':
        subq = ResidentRecord.objects.filter(sex='female').values('pk')
        residents_qs = residents_qs.filter(pk__in=Subquery(subq))
    elif category == 'male':
        subq = ResidentRecord.objects.filter(sex='male').values('pk')
        residents_qs = residents_qs.filter(pk__in=Subquery(subq))
    elif category == 'pwd':
        subq = ResidentRecord.objects.filter(is_pwd=True).values('pk')
        residents_qs = residents_qs.filter(pk__in=Subquery(subq))
    elif category == 'senior':
        subq = ResidentRecord.objects.filter(date_of_birth__lte=senior_cutoff).values('pk')
        residents_qs = residents_qs.filter(pk__in=Subquery(subq))
    elif category == 'underage':
        subq = ResidentRecord.objects.filter(date_of_birth__gt=underage_cutoff).values('pk')
        residents_qs = residents_qs.filter(pk__in=Subquery(subq))
    elif category == 'adults':
        subq = ResidentRecord.objects.filter(
            date_of_birth__lte=underage_cutoff,
            date_of_birth__gt=senior_cutoff
        ).values('pk')
        residents_qs = residents_qs.filter(pk__in=Subquery(subq))

    residents_qs = residents_qs.order_by('-created_at')
    paginator = Paginator(residents_qs, 10)
    residents_page = paginator.get_page(request.GET.get('page'))
    elided_range = paginator.get_elided_page_range(residents_page.number, on_each_side=1, on_ends=1)

    query_params = {}
    if q:
        query_params['q'] = q
    if category:
        query_params['category'] = category
    extra_query = urlencode(query_params)

    sitios = sitios_qs.order_by('name')

    return render(request, 'records/resident_records.html', {
        'residents': residents_page,
        'elided_range': elided_range,
        'extra_query': extra_query,
        'sitios': sitios,
        'q': q,
        'category': category,
        'is_admin': is_admin,
        'assigned_sitio': assigned_sitio,
        'user_skin': _get_user_skin(request.user),
    })


@login_required
def household_records_view(request):
    is_admin, barangay, assigned_sitio = _get_scope(request.user)

    if not is_admin and not assigned_sitio:
        messages.warning(request, "You have not been assigned to a Sitio yet. Please contact your Barangay Admin.")

    if request.method == 'POST':
        action = request.POST.get('action', 'create')
        household_id = request.POST.get('household_id')

        house_number = request.POST.get('house_number', '').strip()
        street = request.POST.get('street', '').strip()
        sitio_id = request.POST.get('sitio_id')
        head_id = request.POST.get('head_of_household_id')
        selected_resident_ids = request.POST.getlist('resident_ids')

        if is_admin:
            sitio_obj = Sitio.objects.filter(pk=sitio_id).first() if sitio_id else None
        else:
            sitio_obj = assigned_sitio

        if not (house_number and sitio_obj):
            messages.error(request, "House Number and Sitio are required.")
            return redirect('records:household_records')

        if action == 'edit' and household_id:
            hh = get_object_or_404(HouseholdRecord, pk=household_id)
            if not is_admin and hh.sitio != assigned_sitio:
                messages.error(request, "You do not have permission to edit households outside your assigned Sitio.")
                return redirect('records:household_records')

            hh.house_number = house_number
            hh.street = street
            hh.sitio = sitio_obj
            hh.updated_by = request.user
            hh.save()

            ResidentRecord.objects.filter(household=hh).exclude(pk__in=selected_resident_ids).update(household=None)
            _log_activity(
                request.user,
                'edit_household',
                f"Edited Household: #{house_number} {street}".strip(),
                sitio=sitio_obj,
                barangay=sitio_obj.barangay,
            )
            messages.success(request, f"Household #{house_number} updated successfully.")
        else:
            hh = HouseholdRecord.objects.create(
                house_number=house_number,
                street=street,
                sitio=sitio_obj,
                created_by=request.user,
                updated_by=request.user,
            )
            _log_activity(
                request.user,
                'add_household',
                f"Added Household: #{house_number} {street}".strip(),
                sitio=sitio_obj,
                barangay=sitio_obj.barangay,
            )
            messages.success(request, f"Household #{house_number} created successfully.")

        if selected_resident_ids:
            ResidentRecord.objects.filter(pk__in=selected_resident_ids).update(
                household=hh,
                sitio=sitio_obj,
                address=hh.full_address,
            )

        if head_id and str(head_id) in [str(rid) for rid in selected_resident_ids]:
            hh.head_of_household_id = head_id
        else:
            hh.head_of_household = None
        hh.save()

        return redirect('records:household_records')

    households_qs = HouseholdRecord.objects.select_related('sitio', 'head_of_household').prefetch_related('household')
    sitios_qs = Sitio.objects.all()

    if is_admin:
        if barangay:
            households_qs = households_qs.filter(sitio__barangay=barangay)
            sitios_qs = sitios_qs.filter(barangay=barangay)
    else:
        if assigned_sitio:
            households_qs = households_qs.filter(sitio=assigned_sitio)
            sitios_qs = sitios_qs.filter(pk=assigned_sitio.pk)
        else:
            households_qs = HouseholdRecord.objects.none()
            sitios_qs = Sitio.objects.none()

    q = request.GET.get('q', '').strip()
    if q:
        households_qs = households_qs.filter(
            Q(house_number__icontains=q) |
            Q(street__icontains=q) |
            Q(sitio__name__icontains=q)
        )

    households_qs = households_qs.annotate(total_members=Count('household')).order_by('-created_at')
    paginator = Paginator(households_qs, 10)
    households_page = paginator.get_page(request.GET.get('page'))
    elided_range = paginator.get_elided_page_range(households_page.number, on_each_side=1, on_ends=1)
    extra_query = urlencode({'q': q}) if q else ''

    sitios = sitios_qs.order_by('name')

    return render(request, 'records/household_records.html', {
        'households': households_page,
        'elided_range': elided_range,
        'extra_query': extra_query,
        'sitios': sitios,
        'q': q,
        'is_admin': is_admin,
        'assigned_sitio': assigned_sitio,
        'user_skin': _get_user_skin(request.user),
    })


@login_required
def search_households_api(request):
    is_admin, barangay, assigned_sitio = _get_scope(request.user)
    q = request.GET.get('q', '').strip()

    qs = HouseholdRecord.objects.select_related('sitio').annotate(total_members=Count('household'))
    if is_admin:
        if barangay:
            qs = qs.filter(sitio__barangay=barangay)
    else:
        qs = qs.filter(sitio=assigned_sitio) if assigned_sitio else HouseholdRecord.objects.none()

    if q:
        for term in q.split():
            clean_term = term.lstrip('#')
            qs = qs.filter(
                Q(house_number__icontains=clean_term) |
                Q(street__icontains=clean_term) |
                Q(sitio__name__icontains=clean_term)
            )

    results = []
    for hh in qs[:8]:
        results.append({
            'id': hh.household_id,
            'full_address': hh.full_address,
            'sitio_id': hh.sitio_id,
            'sitio_name': hh.sitio.name,
            'members': hh.total_members,
        })
    return JsonResponse({'results': results})


@login_required
def search_residents_api(request):
    is_admin, barangay, assigned_sitio = _get_scope(request.user)
    q = request.GET.get('q', '').strip()
    sitio_id = request.GET.get('sitio_id', '').strip()
    household_id = request.GET.get('household_id', '').strip()

    qs = ResidentRecord.objects.select_related('sitio', 'household')
    if is_admin:
        if barangay:
            qs = qs.filter(Q(household__sitio__barangay=barangay) | Q(sitio__barangay=barangay))
        if sitio_id:
            qs = qs.filter(Q(sitio_id=sitio_id) | Q(household__sitio_id=sitio_id) | Q(sitio__isnull=True))
    else:
        qs = qs.filter(Q(sitio=assigned_sitio) | Q(household__sitio=assigned_sitio)) if assigned_sitio else ResidentRecord.objects.none()

    if household_id:
        qs = qs.filter(Q(household__isnull=True) | Q(household_id=household_id))
    else:
        qs = qs.filter(household__isnull=True)

    if q:
        for term in q.split():
            clean_term = term.lstrip('#')
            qs = qs.filter(
                Q(address__icontains=clean_term) |
                Q(first_name__icontains=clean_term) |
                Q(last_name__icontains=clean_term)
            )

    results = []
    for r in qs.order_by('-created_at')[:15]:
        results.append({
            'id': r.resident_id,
            'full_name': f"{r.first_name} {r.last_name}",
            'address': r.display_address,
            'sitio_name': r.display_sitio,
        })
    return JsonResponse({'results': results})