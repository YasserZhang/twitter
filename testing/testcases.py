from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.cache import caches
from django.test import TestCase as DjangoTestCase
from rest_framework.test import APIClient

from comments.models import Comment
from friendships.models import Friendship
from likes.models import Like
from newsfeeds.models import NewsFeed
from newsfeeds.services import NewsFeedService
from tweets.models import Tweet
from utils.redis_client import RedisClient


class TestCase(DjangoTestCase):

    def setUp(self):
        self.clear_cache()
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

    def create_friendship(self, from_user, to_user):
        return Friendship.objects.create(from_user=from_user, to_user=to_user)

    def create_tweet(self, user, content=None):
        if content is None:
            content = 'default tweet content'
        tweet = Tweet.objects.create(user=user, content=content)
        NewsFeedService.fanout_to_followers(tweet)
        return tweet

    def create_tweet_without_fanout(self, user, content=None):
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

    def create_newsfeed(self, user, tweet):
        return NewsFeed.objects.create(user=user, tweet=tweet)

    def create_user_and_client(self, *args, **kwargs):
        user = self.create_user(*args, **kwargs)
        client = APIClient()
        client.force_authenticate(user)
        return user, client

    def clear_cache(self):
        caches['testing'].clear()
        RedisClient.clear()