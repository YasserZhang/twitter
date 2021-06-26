from django.contrib.auth.models import User
from django.db import models
from accounts.services import UserService
# Create your models here.
from django.db.models.signals import pre_delete, post_save

from accounts.listeners import user_changed, profile_changed


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True)
    avatar = models.FileField(null=True)
    nickname = models.CharField(null=True, max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{} {}'.format(self.user, self.nickname)


def get_profile(user):

    if hasattr(user, '_cached_user_profile'):
        return getattr(user, '_cached_user_profile')
    profile = UserService.get_profile_through_cache(user.id)
    setattr(user, '_cached_user_profile', profile)
    return profile


# add profile property to model class User
User.profile = property(get_profile)


# hook up with listeners to invalidate cache
pre_delete.connect(user_changed, sender=User)
post_save.connect(user_changed, sender=User)

pre_delete.connect(profile_changed, sender=UserProfile)
post_save.connect(profile_changed, sender=UserProfile)