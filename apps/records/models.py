from django.db import models
from apps.register.models import User
from apps.core.models import Barangay, Sitio


class HouseholdRecord(models.Model):
    household_id = models.AutoField(primary_key=True)
    created_by = models.ForeignKey(User, on_delete=models.RESTRICT, null=True, related_name='created_households', db_column='created_by')
    updated_by = models.ForeignKey(User, on_delete=models.RESTRICT, null=True, related_name='updated_households', db_column='updated_by')
    head_of_household = models.ForeignKey('ResidentRecord', on_delete=models.SET_NULL, null=True, blank=True, related_name='household_head', db_column='head_of_household_id')
    sitio = models.ForeignKey(Sitio, on_delete=models.CASCADE, related_name='household_records', db_column='sitio_id')

    house_number = models.CharField(max_length=20, blank=True, null=True)
    street = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'household_records'

    @property
    def full_address(self):
        parts = [p for p in [f"#{self.house_number}" if self.house_number else "", self.street or ""] if p]
        return " ".join(parts)

    def __str__(self):
        return f"{self.full_address or self.household_id} ({self.sitio.name})"


class ResidentRecord(models.Model):
    resident_id = models.AutoField(primary_key=True)
    created_by = models.ForeignKey(User, on_delete=models.RESTRICT, null=True, related_name='created_residents', db_column='created_by')
    updated_by = models.ForeignKey(User, on_delete=models.RESTRICT, null=True, related_name='updated_residents', db_column='updated_by')
    household = models.ForeignKey(HouseholdRecord, on_delete=models.SET_NULL, null=True, blank=True, related_name='household', db_column='household_id')
    sitio = models.ForeignKey(Sitio, on_delete=models.SET_NULL, null=True, blank=True, related_name='residents', db_column='sitio_id')
    significant_other = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='partner', db_column='significant_other_id')

    SEX = [('male', 'Male'), ('female', 'Female')]
    CIVIL_STATUS = [
        ('single', 'Single'),
        ('married', 'Married'),
        ('widowed', 'Widowed'),
        ('separated', 'Separated'),
    ]
    STATUS = [
        ('active', 'Active'),
        ('deceased', 'Deceased'),
        ('moved_out', 'Moved Out'),
    ]

    # Personal Information
    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50)
    suffix_name = models.CharField(max_length=50, blank=True, null=True)
    sex = models.CharField(max_length=10, choices=SEX)
    date_of_birth = models.DateField()
    place_of_birth = models.CharField(max_length=100)
    civil_status = models.CharField(max_length=20, choices=CIVIL_STATUS, default='single')
    occupation = models.CharField(max_length=50, blank=True, null=True)
    contact_number = models.CharField(max_length=15, blank=True, null=True)
    voter_status = models.CharField(max_length=50, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    is_pwd = models.BooleanField(default=False)

    # Audit
    status = models.CharField(max_length=20, choices=STATUS, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    encoder = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='encoded_residents')

    class Meta:
        db_table = 'resident_records'

    @property
    def display_address(self):
        if self.household:
            return self.household.full_address or self.address or "—"
        return self.address or "—"

    @property
    def display_sitio(self):
        if self.household and self.household.sitio:
            return self.household.sitio.name
        if self.sitio:
            return self.sitio.name
        return "—"

    def __str__(self):
        return f"{self.last_name}, {self.first_name} ({self.status})"


class ParentChildRelationship(models.Model):
    relationship_id = models.AutoField(primary_key=True)
    parent_resident_id = models.ForeignKey(ResidentRecord, on_delete=models.RESTRICT, null=True, related_name='parent', db_column='parent_resident_id')
    child_resident_id = models.ForeignKey(ResidentRecord, on_delete=models.RESTRICT, null=True, related_name='child', db_column='child_resident_id')

    class Meta:
        db_table = 'parent_child_relationships'

    def __str__(self):
        return f"{self.parent_resident_id.first_name} is the parent of {self.child_resident_id.first_name}"

class ActivityLog(models.Model):
    ACTION_TYPES = [
        ('add_resident', 'Added Resident'),
        ('edit_resident', 'Edited Resident'),
        ('add_household', 'Added Household'),
        ('edit_household', 'Edited Household'),
        ('approve_encoder', 'Approved Encoder'),
        ('decline_encoder', 'Declined Encoder'),
        ('manage_user', 'Managed User'),
        ('add_sitio', 'Added Sitio'),
    ]

    log_id = models.AutoField(primary_key=True)
    barangay = models.ForeignKey(
        Barangay, on_delete=models.CASCADE, null=True, blank=True,
        related_name='activity_logs', db_column='barangay_id'
    )
    sitio = models.ForeignKey(
        Sitio, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='activity_logs', db_column='sitio_id'
    )
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='activity_logs', db_column='user_id'
    )
    user_name = models.CharField(max_length=150)
    role = models.CharField(max_length=30)
    action_type = models.CharField(max_length=30, choices=ACTION_TYPES)
    action_performed = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'activity_logs'
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {self.user_name}: {self.action_performed}"