from django.contrib import admin
from .models import ResidentRecord, HouseholdRecord, ParentChildRelationship

# Register your models here.
admin.site.register(ResidentRecord)
admin.site.register(HouseholdRecord)
admin.site.register(ParentChildRelationship)

