from datetime import timedelta
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.


class CustomUserProfile(AbstractUser):
    tele_number = models.CharField(max_length=25, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    contacts = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='contacted_by')
    is_guest = models.BooleanField(default=False)