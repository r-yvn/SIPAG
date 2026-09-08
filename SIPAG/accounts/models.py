from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    TYPES = [('admin', 'Admin'),('encoder', 'Encoder')]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    barangay = models.CharField(max_length=100, blank=True, null=True)
    type_of_user = models.CharField(max_length=20, choices=TYPES)
    complete_name = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.type_of_user} - {self.complete_name}"
