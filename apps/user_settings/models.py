from django.db import models
from django.conf import settings


class UserSettings(models.Model):
    SKINS = [
        ('default', 'Default (SIPAG Teal)'),
        ('light', 'Soft Light'),
        ('dark', 'Dark Mode'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    dark_mode = models.BooleanField(default=False)
    skin = models.CharField(max_length=20, choices=SKINS, default='default')
    email_notifications = models.BooleanField(default=True)

    class Meta:
        db_table = 'user_settings'

    def __str__(self):
        return f"Settings for {self.user.username}"