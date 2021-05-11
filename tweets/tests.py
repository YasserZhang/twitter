from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase

# Create your tests here.
from tweets.models import Tweet
from utils.time_helpers import utc_now


class TweetTests(TestCase):

    def test_hours_to_now(self):
        a_user = User.objects.create_user(username='a_user')
        tweet = Tweet.objects.create(user=a_user, content="this is my first tweet.")
        tweet.created_at = utc_now() - timedelta(hours=10)
        tweet.save()
        self.assertEqual(tweet.hours_to_now, 10)