from rest_framework.test import APIClient

from testing.testcases import TestCase

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
        self.assertEqual(len(response.data['newsfeeds']), 0)

        # can see user's own tweets
        self.user_a_client.post(POST_TWEET_URL, {'content': 'hello world'})
        response = self.user_a_client.get(NEWSFEED_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['newsfeeds']), 1)

        # follower user_b
        self.user_a_client.post(FOLLOW_URL.format(self.user_b.id))
        response = self.user_b_client.post(POST_TWEET_URL, {'content': 'test tweet by user_b'})
        posted_tweet_id = response.data['id']
        response = self.user_a_client.get(NEWSFEED_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['newsfeeds']), 2)
        self.assertEqual(response.data['newsfeeds'][0]['tweet']['id'], posted_tweet_id)