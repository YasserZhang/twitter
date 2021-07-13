from datetime import timedelta

from django.contrib.auth.models import User


# Create your tests here.
from testing.testcases import TestCase
from tweets.models import Tweet
from tweets.services import TweetService
from twitter.cache_constants import USER_TWEETS_PATTERN
from utils.redis_client import RedisClient
from utils.redis_helper import RedisHelper
from utils.redis_serializers import DjangoModelSerializer
from utils.time_helpers import utc_now


class TweetTests(TestCase):

    def test_hours_to_now(self):
        a_user = User.objects.create_user(username='a_user')
        tweet = Tweet.objects.create(user=a_user, content="this is my first tweet.")
        tweet.created_at = utc_now() - timedelta(hours=10)
        tweet.save()
        self.assertEqual(tweet.hours_to_now, 10)

    def test_cache_tweet_in_redis(self):
        tweet = self.create_tweet(self.user_a)
        conn = RedisClient.get_connection()
        serialized_data = DjangoModelSerializer.serialize(tweet)
        conn.set(f'tweet:{tweet.id}', serialized_data)
        data = conn.get(f'tweet:not_exists')
        self.assertEqual(data, None)

        data = conn.get(f'tweet:{tweet.id}')
        cached_tweet = DjangoModelSerializer.deserialize(data)
        self.assertEqual(tweet, cached_tweet)

class TweetServiceTests(TestCase):

    def setUp(self):
        super().setUp()
        self.clear_cache()

    def test_get_user_tweets(self):
        tweet_ids = []
        for i in range(3):
            tweet = self.create_tweet(self.user_a, 'tweet {}'.format(i))
            tweet_ids.append(tweet.id)
        tweet_ids = tweet_ids[::-1]

        RedisClient.clear() # clean the tweets cache
        conn = RedisClient.get_connection()

        # cache miss
        redis_conn = RedisClient.get_connection()
        key = USER_TWEETS_PATTERN.format(user_id=self.user_a.id)
        cached_objects = RedisHelper.load_objects_from_cache(redis_conn, key)
        self.assertEqual(len(cached_objects), 0)

        # cache hit
        tweets = TweetService.get_cached_tweets(self.user_a.id)
        print(tweets)
        self.assertEqual([t.id for t in tweets], tweet_ids)
        cached_objects = RedisHelper.load_objects_from_cache(redis_conn, key)
        self.assertEqual(len(cached_objects), 3)


