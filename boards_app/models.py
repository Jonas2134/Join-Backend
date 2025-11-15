from django.db import models

from auth_app.models import CustomUserProfile

# Create your models here.

class Boards(models.Model):
    BOARD_STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    owner = models.ForeignKey(CustomUserProfile, on_delete=models.CASCADE, related_name='boards')
    members = models.ManyToManyField(CustomUserProfile, blank=True, related_name='member_boards')
    status = models.CharField(max_length=50, choices=BOARD_STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
