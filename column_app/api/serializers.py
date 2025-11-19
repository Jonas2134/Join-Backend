from rest_framework import serializers
from django.db.models import F
from django.db import transaction

from column_app.models import Column


class ColumnSerializer(serializers.ModelSerializer):
    class Meta:
        model = Column
        fields = ('id', 'name', 'position', 'wip_limit', 'created_at', 'updated_at')


class ColumnCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Column
        fields = ('name', 'wip_limit')

    def save(self, **kwargs):
        board = kwargs.pop('board')
        position = kwargs.pop('position')
        return Column.objects.create(board=board, position=position, **self.validated_data)


class ColumnUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Column
        fields = ('name', 'position', 'wip_limit')

    def update(self, instance, validated_data):
        old_position = instance.position
        new_position = validated_data.get('position', old_position)

        if new_position == old_position:
            return super().update(instance, validated_data)

        board = instance.board

        with transaction.atomic():
            columns = board.columns.order_by('position')

            if new_position > old_position:
                columns.filter(position__gt=old_position, position__lte=new_position).update(position=F('position') - 1)
            else:
                columns.filter(position__lt=old_position, position__gte=new_position).update(position=F('position') + 1)

            instance.position = new_position
            return super().update(instance, validated_data)
