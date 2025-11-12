from datetime import timedelta
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.


class CustomUserProfile(AbstractUser):
    tele_number = models.CharField(max_length=25, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    contacts = models.ManyToManyField(
        'self', symmetrical=False, blank=True, related_name='contacted_by')


class GuestUser(models.Model):
    user = models.OneToOneField(
        CustomUserProfile, on_delete=models.CASCADE, related_name='guest_profile')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'guest_user'

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at
