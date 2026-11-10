from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from apps.records.models import ResidentRecord, HouseholdRecord


@login_required
def home_view(request):
    try:
        total_residents = ResidentRecord.objects.count()
        total_households = HouseholdRecord.objects.count()
        total_male = ResidentRecord.objects.filter(sex='male').count()
        total_female = ResidentRecord.objects.filter(sex='female').count()
        recent_records = ResidentRecord.objects.order_by('-created_at')[:4]
    except Exception:
        total_residents = 0
        total_households = 0
        total_male = 0
        total_female = 0
        recent_records = []

    context = {
        'total_residents': total_residents,
        'total_households': total_households,
        'total_male': total_male,
        'total_female': total_female,
        'total_population': total_residents,
        'recent_records': recent_records,
    }
    return render(request, 'home/home.html', context)
