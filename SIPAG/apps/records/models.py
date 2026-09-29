from django.db import models
from register.models import User
from core.models import Sitio

# Create your models here.
class HouseholdRecord(models.Model):
    household_id = models.AutoField(primary_key=True)
    created_by = models.ForeignKey(User, on_delete=models.RESTRICT, null=True, related_name='created_households', db_column='created_by')
    updated_by = models.ForeignKey(User, on_delete=models.RESTRICT, null=True, related_name='updated_households', db_column='updated_by')
    head_of_household = models.ForeignKey('ResidentRecord', on_delete=models.SET_NULL, null=True, related_name='household_head', db_column='head_of_household_id')
    sitio = models.ForeignKey(Sitio, on_delete=models.CASCADE, related_name='household_records', db_column='sitio_id')

    house_number = models.CharField(max_length=20, blank=True, null=True)
    street = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'household_records'
    
    def __str__(self):
        return f"{self.house_number}"


class ResidentRecord(models.Model):
    resident_id = models.AutoField(primary_key=True)
    created_by = models.ForeignKey(User, on_delete=models.RESTRICT, null=True, related_name='created_residents', db_column='created_by')
    updated_by = models.ForeignKey(User, on_delete=models.RESTRICT, null=True, related_name='updated_residents', db_column='updated_by')
    household = models.ForeignKey(HouseholdRecord, on_delete=models.CASCADE, null=True, related_name='household', db_column='household_id')
    significant_other = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, related_name='partner', db_column='significant_other_id')

    SEX = [('male', 'Male'),('female', 'Female')]
    CIVIL_STATUS = [('single', 'Single'),('married', 'Married'),
                    ('widowed', 'Widowed'),('separated', 'Separated')]  
    STATUS = [('active', 'Active'),('deceased', 'Deceased'),('moved_out', 'Moved Out')]

    #Personal Information
    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50)
    suffix_name = models.CharField(max_length=50, blank=True, null=True)
    sex = models.CharField(max_length=10, choices=SEX)
    date_of_birth = models.DateField()
    place_of_birth = models.CharField(max_length=100)
    civil_status = models.CharField(max_length=20, choices=CIVIL_STATUS)
    occupation = models.CharField(max_length=50, blank=True, null=True)
    contact_number = models.CharField(max_length=15, blank=True, null=True)
    voter_status = models.CharField(max_length=50, blank=True, null=True)

    #Audit
    status = models.CharField(max_length=20, choices=STATUS, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    encoder = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='encoded_residents')

    class Meta:
        db_table = 'resident_records'

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
          


