from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase as DjangoTestCase
from rest_framework.test import APIClient

from comments.models import Comment
from likes.models import Like
from tweets.models import Tweet


class TestCase(DjangoTestCase):

    def setUp(self):
        self.anonymous_client = APIClient()
        self.user_a = self.create_user('user_a')
        self.user_a_client = APIClient()
        self.user_a_client.force_authenticate(self.user_a)

        self.user_b = self.create_user('user_b')
        self.user_b_client = APIClient()
        self.user_b_client.force_authenticate(self.user_b)

    def create_user(self, username, email=None, password=None):
        if password is None:
            password = 'generic passwor'
        return User.objects.create_user(username, email, password)

    def create_tweet(self, user, content=None):
        if content is None:
            content = 'default tweet content'
        return Tweet.objects.create(user=user, content=content)

    def create_comment(self, user, tweet_id, content=None):
        if content is None:
            content = 'default comment'
        return Comment.objects.create(user=user, tweet_id=tweet_id, content=content)

    def create_like(self, user, target):
        instance, _ = Like.objects.get_or_create(
            content_type=ContentType.objects.get_for_model(target.__class__),
            object_id=target.id,
            user=user,
        )
        return instance
