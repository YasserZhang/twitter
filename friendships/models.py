from django.contrib.auth.models import User
from django.db import models

# Create your models here.
from accounts.services import UserService


class Friendship(models.Model):
    from_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='following_friendship_set',
    )
    to_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='follower_friendship_set',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        index_together = (
            ('from_user_id', 'created_at'),
            ('to_user_id', 'created_at')
        )
        unique_together = (("from_user", "to_user"),)

    def __str__(self):
        return '{} followed {}'.format(self.from_user_id, self.to_user_id)

    @property
    def cache_from_user(self):
        UserService.get_profile_through_cache(self.from_user_id)

    def cache_to_user(self):
        UserService.get_profile_through_cache(self.to_user_id)
