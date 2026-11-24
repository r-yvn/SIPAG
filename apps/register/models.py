from django.db import models
from django.contrib.auth.models import AbstractUser
from apps.core.models import Barangay, Sitio


class User(AbstractUser):
    TYPES = [
        ('admin', 'Admin'),
        ('encoder', 'Encoder'),
    ]
    ACCOUNT_STATUS = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
    ]

    email = models.EmailField(unique=True)
    barangay = models.ForeignKey(
        Barangay,
        on_delete=models.CASCADE,
        related_name='users',
        db_column='barangay_id',
        null=True,
        blank=True,
    )
    type_of_user = models.CharField(max_length=20, choices=TYPES, default='encoder')
    account_status = models.CharField(max_length=20, choices=ACCOUNT_STATUS, default='pending')
    contact_number = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user'

    def __str__(self):
        return f"{self.type_of_user} - {self.first_name} {self.last_name}".strip()


class Admin(models.Model):
    admin_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admins', db_column='user_id')

    class Meta:
        db_table = 'admin'

    def __str__(self):
        return f"Admin: {self.user.username}"


class Encoder(models.Model):
    encoder_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='encoders', db_column='user_id')
    sitio = models.ForeignKey(
        Sitio,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='encoders',
        db_column='sitio_id',
    )

    class Meta:
        db_table = 'encoder'

    def __str__(self):
        sitio_name = self.sitio.name if self.sitio else "Unassigned"
        return f"Encoder: {self.user.username} ({sitio_name})"