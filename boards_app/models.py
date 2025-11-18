from django.db import models, transaction

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


class Column(models.Model):
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='columns')
    name = models.CharField(max_length=150)
    position = models.FloatField(default=0)
    wip_limit = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['position']
        constraints = [
            models.UniqueConstraint(fields=['board', 'name'], name='unique_column_per_board')
        ]

    def is_at_wip_limit(self):
        return self.wip_limit is not None and self.tasks.count() >= self.wip_limit

    def available_slots(self):
        if self.wip_limit is None:
            return None
        return max(0, self.wip_limit - self.tasks.count())

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.pk is None:
                last = Column.objects.filter(board=self.board).order_by('-position').first()
                self.position = (last.position + 1) if last else 1
            super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} (Board: {self.board.title})"
