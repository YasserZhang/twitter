from django.contrib.auth.models import User
from django.test import TestCase as DjangoTestCase
from rest_framework.test import APIClient

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