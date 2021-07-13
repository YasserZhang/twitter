from testing.testcases import TestCase
from utils.paginations import EndlessPagination

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
