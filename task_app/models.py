from django.db import models, transaction
from django.core.exceptions import ValidationError

from column_app.models import Column
from auth_app.models import CustomUserProfile

# Create your models here.

class Task(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    column = models.ForeignKey(Column, on_delete=models.CASCADE, related_name='tasks')
    assignee = models.ForeignKey(CustomUserProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    position = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['position']

    def save(self, *args, **kwargs):
        with transaction.atomic():
            original = (
                Task.objects.select_for_update().filter(pk=self.pk).first()
                if self.pk else None
            )
            column_changed = original and original.column_id != self.column_id
            column = Column.objects.select_for_update().get(pk=self.column_id)
            if (self.pk is None or column_changed) and column.wip_limit is not None:
                if column.tasks.count() >= column.wip_limit:
                    raise ValidationError("Cannot add/move task to this column because it reached its WIP limit.")
            creating = self.pk is None
            if creating or column_changed or self.position == 0:
                last = Task.objects.filter(column=self.column).order_by('-position').first()
                self.position =(last.position + 1) if last else 1
            super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} (Column: {self.column.name})"
