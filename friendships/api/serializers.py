from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from accounts.api.serializers import UserSerializerForFriendship
from friendships.models import Friendship
from friendships.services import FriendshipService


class FollowingUserIdSetMixin(serializers.ModelSerializer):

    @property
    def following_user_id_set(self):
        if self.context['request'].user.is_anonymous:
            return {}
        if hasattr(self, '_cached_following_user_id_set'):
            return self._cached_following_user_id_set
        user_id_set = FriendshipService.get_following_user_id_set(
            self.context['request'].user.id,
        )
        setattr(self, '_cached_following_user_id_set', user_id_set)
        return user_id_set


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


class FollowerSerializer(FollowingUserIdSetMixin):
    user = UserSerializerForFriendship(source='cached_from_user')
    created_at = serializers.DateTimeField()
    has_followed = serializers.SerializerMethodField()

    class Meta:
        model = Friendship
        fields = ('user', 'created_at', 'has_followed')

    # def get_has_followed(self, obj):
    #     if self.context['request'].user.is_anonymous:
    #         return False
    #     # TODO: needs to optimize this part
    #     return FriendshipService.has_followed(self.context['request'].user, obj.from_user)

    # among my followers, whom do I also follow back
    def get_has_followed(self, obj):
        return obj.from_user_id in self.following_user_id_set


class FollowingSerializer(FollowingUserIdSetMixin):
    user = UserSerializerForFriendship(source='cached_to_user')
    created_at = serializers.DateTimeField()
    has_followed = serializers.SerializerMethodField()

    class Meta:
        model = Friendship
        fields = ('user', 'created_at', 'has_followed')

    # def get_has_followed(self, obj):
    #     if self.context['request'].user.is_anonymous:
    #         return False
    #     # TODO: need to optimize
    #     return FriendshipService.has_followed(self.context['request'].user, obj.to_user)

    def get_has_followed(self, obj):
        return obj.to_user_id in self.following_user_id_set