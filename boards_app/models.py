from django.db import models

from auth_app.models import CustomUserProfile

# Create your models here.

class Board(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    owner = models.ForeignKey(CustomUserProfile, on_delete=models.CASCADE, related_name='boards')
    members = models.ManyToManyField(CustomUserProfile, blank=True, related_name='member_boards')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
