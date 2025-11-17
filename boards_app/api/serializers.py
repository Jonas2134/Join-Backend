from rest_framework import serializers

from auth_app.models import CustomUserProfile
from boards_app.models import Boards


class BoardListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Boards
        fields = ('id', 'title', 'status')


class BoardCreateSerializer(serializers.ModelSerializer):
    members = serializers.PrimaryKeyRelatedField(queryset=CustomUserProfile.objects.all(), many=True, required=False, allow_empty=True)
    
    class Meta:
        model = Boards
        fields = ('title', 'description', 'members')

    def validate(self, attrs):
        request = self.context['request']
        if request.user.is_guest and 'members' in attrs and len(attrs['members']) > 0:
            raise serializers.ValidationError("Guest users cannot add members to boards.")
        return attrs
    
    def create(self, validated_data):
        request = self.context['request']
        members = validated_data.pop('members', [])
        board = Boards.objects.create(owner=request.user, **validated_data)
        final_members = set(members)
        final_members.add(request.user)
        board.members.set(final_members)
        return board
