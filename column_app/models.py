from django.db import models, transaction
from django.db.models import F

from board_app.models import Board

# Create your models here.


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
            models.UniqueConstraint(
                fields=['board', 'name'], name='unique_column_per_board')
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
    
    def delete(self, *args, **kwargs):
        board = self.board
        position = self.position
        with transaction.atomic():
            super().delete(*args, **kwargs)
            board.columns.filter(position__gt=position).update(position=F('position') - 1)

    def __str__(self):
        return f"{self.name} (Board: {self.board.title})"
