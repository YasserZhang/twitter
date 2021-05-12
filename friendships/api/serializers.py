from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from accounts.api.serializers import UserSerializer
from friendships.models import Friendship


class FriendshipSerializerForCreate(serializers.ModelSerializer):
    from_user_id = serializers.IntegerField()
    to_user_id = serializers.IntegerField()

    class Meta:
        model = Friendship
        fields = ('from_user_id', 'to_user_id')

    def validate(self, data):
        if data['from_user_id'] == data['to_user_id']:
            raise ValidationError({
                'message': 'from_user_id and to_user_id should not be the same.'
            })
        return data

    def create(self, validated_data):
        friendship = Friendship.objects.create(
            from_user_id=validated_data['from_user_id'],
            to_user_id=validated_data['to_user_id'])
        return friendship


class FollowerSerializer(serializers.ModelSerializer):
    user = UserSerializer(source='from_user')
    created_at = serializers.DateTimeField()

    class Meta:
        model = Friendship
        fields = ('user', 'created_at')


class FollowingSerializer(serializers.ModelSerializer):
    user = UserSerializer(source='to_user')
    created_at = serializers.DateTimeField()

    class Meta:
        model = Friendship
        fields = ('user', 'created_at')