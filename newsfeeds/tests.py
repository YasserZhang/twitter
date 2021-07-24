from newsfeeds.models import NewsFeed
from newsfeeds.services import NewsFeedService
from newsfeeds.tasks import fanout_newsfeeds_main_task
from testing.testcases import TestCase
from utils.redis_client import RedisClient


class NewsFeedsServiceTests(TestCase):

    def test_get_user_newsfeeds(self):
        newsfeed_ids = []
        for i in range(3):
            tweet = self.create_tweet(self.user_a)
            newsfeed = self.create_newsfeed(self.user_b, tweet)
            newsfeed_ids.append(newsfeed.id)
        newsfeed_ids = newsfeed_ids[::-1]

        RedisClient.clear()

        # cache miss
        newsfeeds = NewsFeedService.get_cached_newsfeeds(self.user_b.id)
        self.assertEqual([f.id for f in newsfeeds], newsfeed_ids)

        # cache hit
        newsfeeds = NewsFeedService.get_cached_newsfeeds(self.user_b.id)
        self.assertEqual([f.id for f in newsfeeds], newsfeed_ids)

        # cache updated
        tweet = self.create_tweet(self.user_a)
        new_newsfeed = self.create_newsfeed(self.user_b, tweet)
        newsfeeds = NewsFeedService.get_cached_newsfeeds(self.user_b.id)
        newsfeed_ids.insert(0, new_newsfeed.id)
        self.assertEqual([f.id for f in newsfeeds], newsfeed_ids)

class NewsFeedTaskTests(TestCase):

    def test_fanout_main_task(self):
        tweet = self.create_tweet_without_fanout(self.user_a, 'tweet 1')
        self.create_friendship(self.user_b, self.user_a)
        msg = fanout_newsfeeds_main_task(tweet.id, tweet.user_id)
        self.assertEqual(msg, '1 newsfeeds going to fanout, 1 batches created.')
        self.assertEqual(1 + 1, NewsFeed.objects.count())
        cached_list = NewsFeedService.get_cached_newsfeeds(self.user_a.id)
        self.assertEqual(len(cached_list), 1)

        for i in range(2):
            user = self.create_user('user{}'.format(i))
            self.create_friendship(user, self.user_a)
        tweet = self.create_tweet_without_fanout(self.user_a, 'tweet 2')
        msg = fanout_newsfeeds_main_task(tweet.id, self.user_a.id)
        # user_a has 3 followers now
        self.assertEqual(msg, '3 newsfeeds going to fanout, 1 batches created.')
        self.assertEqual(4 + 2, NewsFeed.objects.count())
        cached_list = NewsFeedService.get_cached_newsfeeds(self.user_a.id)
        self.assertEqual(len(cached_list), 2)

        user = self.create_user('another user')
        self.create_friendship(user, self.user_a)
        tweet = self.create_tweet_without_fanout(self.user_a, 'tweet 3')
        msg = fanout_newsfeeds_main_task(tweet.id, self.user_a.id)
        self.assertEqual(msg, '4 newsfeeds going to fanout, 2 batches created.')
        self.assertEqual(8 + 3, NewsFeed.objects.count())
        cached_list = NewsFeedService.get_cached_newsfeeds(self.user_a.id)
        self.assertEqual(len(cached_list), 3)
        cached_list = NewsFeedService.get_cached_newsfeeds(self.user_b.id)
        self.assertEqual(len(cached_list), 3)
