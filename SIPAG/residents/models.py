from django.db import models
from django.contrib.auth.models import User

class Resident(models.Model):
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
    occupation = models.CharField(max_length=100, blank=True, null=True)
    contact_number = models.CharField(max_length=20, blank=True, null=True)

    #Household Information
    purok = models.CharField(max_length=50)
    house_number = models.CharField(max_length=20, blank=True, null=True)
    street = models.CharField(max_length=200, blank=True, null=True)
    is_head_of_household = models.BooleanField(default=False)

    #Audit
    status = models.CharField(max_length=20, choices=STATUS, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    encoder = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='encoded_residents')

    def __str__(self):
        return f"{self.last_name}, {self.first_name} ({self.status})"