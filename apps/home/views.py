from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from apps.core.models import Sitio
from apps.records.models import HouseholdRecord, ResidentRecord

User = get_user_model()


@login_required
def home_view(request):
    today = date.today()
    underage_cutoff = today - timedelta(days=18 * 365.25)
    senior_cutoff = today - timedelta(days=60 * 365.25)

    try:
        total_residents = ResidentRecord.objects.count()
        total_households = HouseholdRecord.objects.count()
        total_male = ResidentRecord.objects.filter(sex='male').count()
        total_female = ResidentRecord.objects.filter(sex='female').count()
        total_sitios = Sitio.objects.count()
        active_users = User.objects.filter(is_active=True).count()

        # Age categories
        total_underage = ResidentRecord.objects.filter(date_of_birth__gt=underage_cutoff).count()
        total_seniors = ResidentRecord.objects.filter(date_of_birth__lte=senior_cutoff).count()
        total_adults = ResidentRecord.objects.filter(
            date_of_birth__lte=underage_cutoff,
            date_of_birth__gt=senior_cutoff
        ).count()
        total_pwd = 0

        # Recent actions / logs
        recent_records = ResidentRecord.objects.select_related('created_by', 'household__sitio').order_by('-created_at')[:8]
        recent_actions = []
        for rec in recent_records:
            recent_actions.append({
                'timestamp': rec.created_at.strftime('%Y-%m-%d %H:%M') if rec.created_at else '—',
                'user': rec.created_by.get_full_name() or rec.created_by.username if rec.created_by else 'System',
                'role': rec.created_by.type_of_user.title() if (rec.created_by and hasattr(rec.created_by, 'type_of_user')) else 'Encoder',
                'action_performed': f"Added Resident: {rec.first_name} {rec.last_name}",
                'sitio': rec.household.sitio.name if (rec.household and rec.household.sitio) else '—',
            })
    except Exception:
        total_residents = 0
        total_households = 0
        total_male = 0
        total_female = 0
        total_sitios = 0
        active_users = 0
        total_underage = 0
        total_seniors = 0
        total_adults = 0
        total_pwd = 0
        recent_actions = []

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
        'recent_actions': recent_actions,
    }

    # Determine user role and render appropriate dashboard
    user = request.user
    is_admin = getattr(user, 'type_of_user', '') == 'admin' or user.is_staff or user.is_superuser

    if is_admin:
        return render(request, 'dashboard/admin_dashboard.html', context)
    else:
        return render(request, 'dashboard/encoder_dashboard.html', context)
