from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from accounts.api.serializers import UserSerializer
from friendships.models import Friendship


class FriendshipSerializerForCreate(serializers.ModelSerializer):
    # from_user = UserSerializer()
    # to_user = UserSerializer()
    from_user_id = serializers.IntegerField()
    to_user_id = serializers.IntegerField()

    class Meta:
        model = Friendship
        # fields = ('from_user', 'to_user', 'created_at')
        fields = ('from_user_id', 'to_user_id')

    def validate(self, attrs):
        if attrs['from_user_id'] == attrs['to_user_id']:
            raise ValidationError({
                'message': 'from_user_id and to_user_id should be different'
            })
        return attrs

    def create(self, validated_data):
        from_user_id = validated_data['from_user_id']
        to_user_id = validated_data['to_user_id']
        return Friendship.objects.create(
            from_user_id=from_user_id,
            to_user_id=to_user_id,
        )

    # def validate(self, data):
    #     if data['from_user']['id'] == data['to_user_id']:
    #         raise ValidationError({
    #             'message': 'from_user_id and to_user_id should be different.'
    #         })
    #     return data
    #
    # def create(self, validated_data):
    #     from_user = validated_data.from_user
    #     to_user_id = validated_data.to_user_id
    #     friendship = Friendship.objects.create(from_user=from_user, to_user_id=to_user_id)
    #     return friendship


class FollowerSerializer(serializers.ModelSerializer):
    user = UserSerializer(source='from_user')
    created_at = serializers.DateTimeField()

    class Meta:
        model = Friendship
        fields = ('from_user', 'created_at')


class FollowingSerializer(serializers.ModelSerializer):
    user = UserSerializer(source='to_user')
    created_at = serializers.DateTimeField()

    class Meta:
        model = Friendship
        fields = ('to_user', 'created_at')