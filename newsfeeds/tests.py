from newsfeeds.services import NewsFeedService
from testing.testcases import TestCase
from utils.redis_client import RedisClient
from utils.redis_helper import RedisHelper


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
