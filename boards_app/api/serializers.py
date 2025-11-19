from rest_framework import serializers

from auth_app.models import CustomUserProfile
from boards_app.models import Board, Column


class BoardListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Board
        fields = ('id', 'title', 'is_active')


class BoardCreateSerializer(serializers.ModelSerializer):
    members = serializers.PrimaryKeyRelatedField(queryset=CustomUserProfile.objects.all(), many=True, required=False, allow_empty=True)
    
    class Meta:
        model = Board
        fields = ('title', 'description', 'members')

    def validate(self, attrs):
        request = self.context['request']
        if request.user.is_guest and 'members' in attrs and len(attrs['members']) > 0:
            raise serializers.ValidationError("Guest users cannot add members to boards.")
        return attrs
    
    def create(self, validated_data):
        request = self.context['request']
        members = validated_data.pop('members', [])
        board = Board.objects.create(owner=request.user, **validated_data)
        final_members = set(members)
        final_members.add(request.user)
        board.members.set(final_members)
        return board


class BoardDetailSerializer(serializers.ModelSerializer):
    members = serializers.PrimaryKeyRelatedField(queryset=CustomUserProfile.objects.all(), many=True)
    
    class Meta:
        model = Board
        fields = ('id', 'title', 'description', 'owner', 'members', 'is_active', 'created_at', 'updated_at')


class BoardUpdateSerializer(serializers.ModelSerializer):
    members = serializers.PrimaryKeyRelatedField(queryset=CustomUserProfile.objects.all(), many=True, required=False)
    
    class Meta:
        model = Board
        fields = ('title', 'description', 'members', 'is_active')

    def validate(self, attrs):
        request = self.context['request']
        if "owner" in attrs:
            attrs.pop("owner")
        if request.user.is_guest and 'members' in attrs:
            raise serializers.ValidationError("Guest users cannot modify board members.")
        return attrs

    def update(self, instance, validated_data):
        members = validated_data.pop('members', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if members is not None:
            final_members = set(members)
            final_members.add(instance.owner)
            instance.members.set(final_members)
        instance.save()
        return instance


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
