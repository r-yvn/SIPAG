from django.contrib import admin
from .models import ActivityLog, ResidentRecord, HouseholdRecord, ParentChildRelationship

# Register your models here.
admin.site.register(ResidentRecord)
admin.site.register(HouseholdRecord)
admin.site.register(ParentChildRelationship)
admin.site.register(ActivityLog)

