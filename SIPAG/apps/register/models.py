from django.db import models
from django.contrib.auth.models import AbstractUser
from core.models import Barangay, Sitio

class User(AbstractUser):
    TYPES = [('admin', 'Admin'),('encoder', 'Encoder')]

    barangay = models.ForeignKey(Barangay, on_delete=models.CASCADE, related_name='users', db_column='barangay_id', null=True, blank=True)
    type_of_user = models.CharField(max_length=20, choices=TYPES)
    contact_number = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta: 
        db_table = 'user'

    def __str__(self):
        return f"{self.type_of_user} - {self.first_name} {self.last_name}"


class Admin(models.Model):
    admin_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admins', db_column='user_id')

    class Meta:
        db_table = 'admin'

    def __str__(self):
        return self
    
class Encoder(models.Model):
    encoder_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='encoders', db_column='user_id')
    sitio = models.ForeignKey(Sitio, on_delete=models.CASCADE, related_name='encoders', db_column='sitio_id')

    class Meta:
        db_table = 'encoder'

    def __str__(self):
            return self    
        
