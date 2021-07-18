from newsfeeds.models import NewsFeed
from newsfeeds.services import NewsFeedService
from testing.testcases import TestCase
from twitter import settings
from utils.paginations import EndlessPagination
from utils.redis_client import RedisClient

NEWSFEED_URL = '/api/newsfeeds/'
POST_TWEET_URL = '/api/tweets/'
FOLLOW_URL = '/api/friendships/{}/follow/'


class NewsFeedTestCase(TestCase):

    def test_list(self):
        # anonymous client not allowed
        response = self.anonymous_client.get(NEWSFEED_URL)
        self.assertEqual(response.status_code, 403)

        # POST method not allowed
        response = self.user_a_client.post(NEWSFEED_URL)
        self.assertEqual(response.status_code, 405)

        # successful GET
        response = self.user_a_client.get(NEWSFEED_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 0)

        # can see user's own tweets
        self.user_a_client.post(POST_TWEET_URL, {'content': 'hello world'})
        response = self.user_a_client.get(NEWSFEED_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)

        # follower user_b
        self.user_a_client.post(FOLLOW_URL.format(self.user_b.id))
        response = self.user_b_client.post(POST_TWEET_URL, {'content': 'test tweet by user_b'})
        posted_tweet_id = response.data['id']
        response = self.user_a_client.get(NEWSFEED_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['results'][0]['tweet']['id'], posted_tweet_id)

    def test_pagination(self):
        page_size = EndlessPagination.page_size
        followed_user = self.create_user('followed')
        newsfeeds = []
        for i in range(page_size * 2):
            tweet = self.create_tweet(followed_user)
            newsfeed = self.create_newsfeed(user=self.user_a, tweet=tweet)
            newsfeeds.append(newsfeed)
        newsfeeds = newsfeeds[::-1]

        # pull the first page
        response = self.user_a_client.get(NEWSFEED_URL)
        self.assertEqual(response.data['has_next_page'], True)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['results'][0]['id'], newsfeeds[0].id)
        self.assertEqual(response.data['results'][1]['id'], newsfeeds[1].id)
        self.assertEqual(
            response.data['results'][page_size - 1]['id'],
            newsfeeds[page_size - 1].id,
        )

        # pull the second page
        response = self.user_a_client.get(
            NEWSFEED_URL,
            {'created_at__lt': newsfeeds[page_size - 1].created_at},
        )
        self.assertEqual(response.data['has_next_page'], False)
        results = response.data['results']
        self.assertEqual(len(results), page_size)
        self.assertEqual(results[0]['id'], newsfeeds[page_size].id)
        self.assertEqual(results[1]['id'], newsfeeds[page_size+1].id)
        self.assertEqual(results[page_size-1]['id'], newsfeeds[page_size * 2 - 1].id)

        # pull latest newsfeeds
        response = self.user_a_client.get(
            NEWSFEED_URL,
            {'created_at__gt': newsfeeds[0].created_at},
        )
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), 0)

        tweet = self.create_tweet(followed_user)
        new_newsfeed = self.create_newsfeed(self.user_a, tweet)

        response = self.user_a_client.get(
            NEWSFEED_URL,
            {'created_at__gt': newsfeeds[0].created_at},
        )
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], new_newsfeed.id)

    def test_tweet_cache(self):
        tweet = self.create_tweet(self.user_a, 'content1')
        self.create_newsfeed(self.user_b, tweet)
        response = self.user_b_client.get(NEWSFEED_URL)
        results = response.data['results']
        self.assertEqual(results[0]['tweet']['user']['username'], 'user_a')
        self.assertEqual(results[0]['tweet']['content'], 'content1')

        # update username
        self.user_a.username = 'new_user_a'
        self.user_a.save()
        response = self.user_b_client.get(NEWSFEED_URL)
        results = response.data['results']
        self.assertEqual(results[0]['tweet']['user']['username'], 'new_user_a')

        # update content
        tweet.content = 'content2'
        tweet.save()
        response = self.user_b_client.get(NEWSFEED_URL)
        results = response.data['results']
        self.assertEqual(results[0]['tweet']['content'], 'content2')

    def _paginate_to_get_newsfeeds(self, client):
        # paginate until the end
        response = client.get(NEWSFEED_URL)
        results = response.data['results']
        while response.data['has_next_page']:
            created_at__lt = response.data['results'][-1]['created_at']
            response = client.get(NEWSFEED_URL, {'created_at__lt': created_at__lt})
            results.extend(response.data['results'])
        return results

    def test_redis_list_limit(self):
        list_limit = settings.REDIS_LIST_LENGTH_LIMIT
        print("list_limit", list_limit)
        page_size = 20
        users = [self.create_user('user{}'.format(i)) for i in range(5)]
        newsfeeds = []
        for i in range(list_limit + page_size):
            tweet = self.create_tweet(user=users[i % 5], content='feed{}'.format(i))
            newsfeed = self.create_newsfeed(self.user_a, tweet)
            newsfeeds.append(newsfeed)
        newsfeeds = newsfeeds[::-1]

        # only cache list_limit objects
        cached_newsfeeds = NewsFeedService.get_cached_newsfeeds(self.user_a.id)
        self.assertEqual(len(cached_newsfeeds), list_limit)
        queryset = NewsFeed.objects.filter(user=self.user_a)
        self.assertEqual(queryset.count(), list_limit + page_size)

        results = self._paginate_to_get_newsfeeds(self.user_a_client)
        self.assertEqual(len(results), list_limit + page_size)
        for i in range(list_limit + page_size):
            self.assertEqual(newsfeeds[i].id, results[i]['id'])

        # a followed user create a new tweet
        self.create_friendship(self.user_a, self.user_b)
        new_tweet = self.create_tweet(self.user_b, "a new tweet")

        def _test_newsfeeds_after_new_feed_pushed():
            results = self._paginate_to_get_newsfeeds(self.user_a_client)
            self.assertEqual(len(results), list_limit + page_size + 1)
            self.assertEqual(results[0]['tweet']['id'], new_tweet.id)
            for i in range(list_limit + page_size):
                self.assertEqual(newsfeeds[i].id, results[i+1]['id'])

        _test_newsfeeds_after_new_feed_pushed()

        # cache expired
        self.clear_cache()
        _test_newsfeeds_after_new_feed_pushed()



