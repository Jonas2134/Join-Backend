from rest_framework import serializers

from tasks_app.models import Task

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ('id', 'title', 'description', 'column', 'assignee', 'position', 'created_at', 'updated_at')


class TaskCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ('title', 'description', 'assignee')

    def save(self, **kwargs):
        column = kwargs.pop('column')
        position = kwargs.pop('position')
        return Task.objects.create(column=column, position=position, **self.validated_data)


class TaskUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ('title', 'description', 'assignee', 'column', 'position')
