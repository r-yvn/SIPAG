from datetime import date, datetime, time, timedelta
from urllib.parse import urlencode
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
from django.utils import timezone
from apps.core.models import Sitio
from apps.records.models import ActivityLog, HouseholdRecord, ResidentRecord
from apps.register.models import Encoder
from apps.user_settings.models import UserSettings

User = get_user_model()


def subtract_years(d, years):
    try:
        return d.replace(year=d.year - years)
    except ValueError:
        return d.replace(month=2, day=28, year=d.year - years)


def get_user_skin(user):
    settings_obj, _ = UserSettings.objects.get_or_create(user=user)
    return settings_obj.skin or ('dark' if settings_obj.dark_mode else 'default')


def get_current_week_range():
    now = timezone.now()
    if getattr(settings, 'USE_TZ', False) and timezone.is_aware(now):
        now = timezone.localtime(now)
    today = now.date()
    days_since_sunday = (today.weekday() + 1) % 7
    week_start_date = today - timedelta(days=days_since_sunday)
    week_end_date = week_start_date + timedelta(days=6)

    start_dt = datetime.combine(week_start_date, time.min)
    end_dt = datetime.combine(week_end_date, time.max)
    if getattr(settings, 'USE_TZ', False):
        tz = timezone.get_current_timezone()
        start_dt = timezone.make_aware(start_dt, tz)
        end_dt = timezone.make_aware(end_dt, tz)
    return start_dt, end_dt, week_start_date, week_end_date


@login_required
def home_view(request):
    today = date.today()
    underage_cutoff = subtract_years(today, 18)
    senior_cutoff = subtract_years(today, 60)

    user = request.user
    is_admin = getattr(user, 'type_of_user', '') == 'admin' or user.is_staff or user.is_superuser
    user_skin = get_user_skin(user)

    if is_admin:
        if user.barangay:
            residents_qs = ResidentRecord.objects.filter(
                Q(household__sitio__barangay=user.barangay) | Q(sitio__barangay=user.barangay)
            )
            households_qs = HouseholdRecord.objects.filter(sitio__barangay=user.barangay)
            sitios_qs = Sitio.objects.filter(barangay=user.barangay)
            active_users = User.objects.filter(is_active=True, barangay=user.barangay).count()
        else:
            residents_qs = ResidentRecord.objects.all()
            households_qs = HouseholdRecord.objects.all()
            sitios_qs = Sitio.objects.all()
            active_users = User.objects.filter(is_active=True).count()
    else:
        encoder_obj = Encoder.objects.filter(user=user).select_related('sitio').first()
        assigned_sitio = encoder_obj.sitio if encoder_obj else None
        if assigned_sitio:
            residents_qs = ResidentRecord.objects.filter(
                Q(household__sitio=assigned_sitio) | Q(sitio=assigned_sitio)
            )
            households_qs = HouseholdRecord.objects.filter(sitio=assigned_sitio)
            sitios_qs = Sitio.objects.filter(pk=assigned_sitio.pk)
        else:
            residents_qs = ResidentRecord.objects.none()
            households_qs = HouseholdRecord.objects.none()
            sitios_qs = Sitio.objects.none()
        active_users = 1

    total_residents = residents_qs.count()
    total_households = households_qs.count()
    total_male = residents_qs.filter(sex='male').count()
    total_female = residents_qs.filter(sex='female').count()
    total_sitios = sitios_qs.count()
    total_underage = residents_qs.filter(date_of_birth__gt=underage_cutoff).count()
    total_seniors = residents_qs.filter(date_of_birth__lte=senior_cutoff).count()
    total_adults = residents_qs.filter(
        date_of_birth__lte=underage_cutoff,
        date_of_birth__gt=senior_cutoff
    ).count()
    total_pwd = residents_qs.filter(is_pwd=True).count()

    # Admin Dashboard: Recent Actions strictly within the current week + paginated
    week_start, week_end, week_start_date, week_end_date = get_current_week_range()
    action_type = request.GET.get('action_type', '').strip()

    logs_qs = ActivityLog.objects.select_related('sitio').filter(
        timestamp__gte=week_start,
        timestamp__lte=week_end,
    )
    if user.barangay:
        logs_qs = logs_qs.filter(barangay=user.barangay)
    if action_type:
        logs_qs = logs_qs.filter(action_type=action_type)

    paginator = Paginator(logs_qs, 8)
    actions_page = paginator.get_page(request.GET.get('page'))
    actions_elided_range = paginator.get_elided_page_range(actions_page.number, on_each_side=1, on_ends=1)
    extra_query = urlencode({'action_type': action_type}) if action_type else ''

    context = {
        'total_residents': total_residents,
        'total_population': total_residents,
        'total_households': total_households,
        'total_male': total_male,
        'total_female': total_female,
        'total_sitios': total_sitios,
        'active_users': active_users,
        'total_underage': total_underage,
        'total_seniors': total_seniors,
        'total_adults': total_adults,
        'total_pwd': total_pwd,
        'actions_page': actions_page,
        'actions_elided_range': actions_elided_range,
        'action_types': ActivityLog.ACTION_TYPES,
        'selected_action_type': action_type,
        'week_start_date': week_start_date,
        'week_end_date': week_end_date,
        'extra_query': extra_query,
        'user_skin': user_skin,
    }

    if is_admin:
        return render(request, 'dashboard/admin_dashboard.html', context)
    return render(request, 'dashboard/encoder_dashboard.html', context)