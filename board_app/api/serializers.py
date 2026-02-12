from rest_framework import serializers

from auth_app.models import CustomUserProfile
from board_app.models import Board
from column_app.api.serializers import ColumnSerializer
from contact_and_profile_app.api.serializers import MemberNestedSerializer


class BoardListSerializer(serializers.ModelSerializer):
    member_count = serializers.SerializerMethodField()
    is_user_owner = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = ('id', 'title', 'member_count', 'is_user_owner', 'is_active')

    def get_member_count(self, obj):
        return obj.members.count()

    def get_is_user_owner(self, obj):
        return self.context['request'].user == obj.owner


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
    members = MemberNestedSerializer(many=True, read_only=True)
    columns = ColumnSerializer(many=True, read_only=True)
    
    class Meta:
        model = Board
        fields = ('id', 'title', 'description', 'owner', 'members', 'columns', 'is_active', 'created_at', 'updated_at')


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
