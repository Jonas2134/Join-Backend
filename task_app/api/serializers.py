from rest_framework import serializers
from django.db.models import F
from django.db import transaction

from task_app.models import Task
from column_app.models import Column

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ('id', 'title', 'description', 'column', 'assignee', 'position', 'created_at', 'updated_at')


class TaskCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ('title', 'description', 'assignee')

    def validate_assignee(self, value):
        column_pk = self.context["view"].kwargs.get("column_pk")
        if not column_pk:
            raise serializers.ValidationError("ID not found!")
        try:
            column = Column.objects.get(pk=column_pk)
        except Column.DoesNotExist:
            raise serializers.ValidationError("Column not found!")
        board = column.board
        if not board.members.filter(id=value.id).exists():
            raise serializers.ValidationError("Assignee is not a member!")
        return value

    def validate(self, attrs):
        column_pk = self.context["view"].kwargs.get("column_pk")
        try:
            column = Column.objects.get(pk=column_pk)
        except Column.DoesNotExist:
            raise serializers.ValidationError("Column not found!")
        # Pre-check for better error message; Task.save() enforces this atomically.
        if column.is_at_wip_limit():
            raise serializers.ValidationError(
                f"Column '{column.name}' has reached its WIP limit ({column.wip_limit})."
            )
        return attrs

    def save(self, **kwargs):
        column = kwargs.pop('column')
        return Task.objects.create(column=column, **self.validated_data)


class TaskUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ('title', 'description', 'assignee', 'column', 'position')

    def validate_assignee(self, value):
        task_pk = self.context["view"].kwargs.get("task_pk")
        try:
            task = Task.objects.get(pk=task_pk)
        except Task.DoesNotExist:
            raise serializers.ValidationError("Task not found!")
        board = task.column.board
        if not board.members.filter(id=value.id).exists():
            raise serializers.ValidationError("Assignee is not a member!")
        return value

    def validate_column(self, value):
        instance = getattr(self, 'instance', None)
        if instance:
            if value.board != instance.column.board:
                raise serializers.ValidationError("Column is not in the board!")
            if value != instance.column and value.is_at_wip_limit():
                raise serializers.ValidationError(
                    f"Column '{value.name}' has reached its WIP limit ({value.wip_limit})."
                )
        return value

    def update(self, instance, validated_data):
        old_pos = instance.position
        old_col = instance.column
        new_pos = validated_data.get('position', old_pos)
        new_col = validated_data.get('column', old_col)
        with transaction.atomic():
            old_col = Column.objects.select_for_update().get(pk=old_col.pk)
            new_col = Column.objects.select_for_update().get(pk=new_col.pk)
            if old_col == new_col:
                if new_pos != old_pos:
                    qs = old_col.tasks.order_by('position')
                    if new_pos > old_pos:
                        qs.filter(position__gt=old_pos, position__lte=new_pos).update(position=F('position') - 1)
                    else:
                        qs.filter(position__lt=old_pos, position__gte=new_pos).update(position=F('position') + 1)
            else:
                old_col.tasks.filter(position__gt=old_pos).update(position=F('position') - 1)
                qs_new = new_col.tasks.exclude(pk=instance.pk).order_by('position')
                max_pos = qs_new.count() + 1
                if new_pos > max_pos:
                    new_pos = max_pos
                qs_new.filter(position__gte=new_pos).update(position=F('position') + 1)
            
            for field in ("title", "description", "assignee"):
                if field in validated_data:
                    setattr(instance, field, validated_data[field])
            instance.column = new_col
            instance.position = new_pos
            instance.save()
            return instance
