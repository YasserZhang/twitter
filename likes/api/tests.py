from friendships.models import Friendship
from testing.testcases import TestCase

LIKE_BASE_URL='/api/likes/'
LIKE_CANCEL_URL = '/api/likes/cancel/'
COMMENT_LIST_API = '/api/comments/'
TWEET_LIST_API = '/api/tweets/'
TWEET_DETAIL_API = '/api/tweets/{}/'
NEWSFEED_LIST_API = '/api/newsfeeds/'
FOLLOW_URL = '/api/friendships/{}/follow/'

class LikeApiTest(TestCase):

    def test_tweet_likes(self):
        tweet = self.create_tweet(self.user_a)
        data = {'content_type': 'tweet', 'object_id': tweet.id}

        response = self.anonymous_client.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 403)

        response = self.user_b_client.get(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 405)

        response = self.user_b_client.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(tweet.like_set.count(), 1)

        # duplicate likes
        self.user_b_client.post(LIKE_BASE_URL, data)
        self.assertEqual(tweet.like_set.count(), 1)
        self.user_a_client.post(LIKE_BASE_URL, data)
        self.assertEqual(tweet.like_set.count(), 2)

    def test_comment_likes(self):
        tweet = self.create_tweet(self.user_a)
        comment = self.create_comment(self.user_a, tweet.id)
        data = {'content_type': 'comment', 'object_id': comment.id}

        response = self.anonymous_client.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 403)

        response = self.user_b_client.get(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 405)

        response = self.user_b_client.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(comment.like_set.count(), 1)

        # duplicate likes
        self.user_b_client.post(LIKE_BASE_URL, data)
        self.assertEqual(comment.like_set.count(), 1)
        self.user_a_client.post(LIKE_BASE_URL, data)
        self.assertEqual(comment.like_set.count(), 2)

    def test_tweet_cancel_likes(self):
        tweet = self.create_tweet(self.user_a)
        data = {'content_type': 'tweet', 'object_id': tweet.id}

        response = self.user_b_client.post(LIKE_CANCEL_URL, data)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(tweet.like_set.count(), 0)
        self.user_b_client.post(LIKE_BASE_URL, data)
        self.assertEqual(tweet.like_set.count(), 1)
        response = self.user_b_client.post(LIKE_CANCEL_URL, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(tweet.like_set.count(), 0)

    def test_comment_cancel_likes(self):
        tweet = self.create_tweet(self.user_a)
        comment = self.create_comment(self.user_a, tweet.id)
        data = {'content_type': 'comment', 'object_id': comment.id}

        # nothing should happen when cancel a non-existent like
        response = self.user_b_client.post(LIKE_CANCEL_URL, data)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(comment.like_set.count(), 0)
        self.user_b_client.post(LIKE_BASE_URL, data)
        self.assertEqual(comment.like_set.count(), 1)
        response = self.user_b_client.post(LIKE_CANCEL_URL, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(comment.like_set.count(), 0)

    def test_likes_in_tweets_api(self):
        self.user_b_client.post(FOLLOW_URL.format(self.user_a.id))
        self.assertEqual(Friendship.objects.count(), 1)

        tweet = self.create_tweet(self.user_a)
        data = {'content_type': 'tweet', 'object_id': tweet.id}

        tweet_detail_url = TWEET_DETAIL_API.format(tweet.id)
        response = self.user_b_client.get(tweet_detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['has_liked'], False)
        self.assertEqual(response.data['likes_count'], 0)
        # user_b likes user_a's tweet
        self.create_like(self.user_b, tweet)
        # retrieve tweet details
        response = self.user_b_client.get(tweet_detail_url)
        self.assertEqual(response.data['has_liked'], True)
        self.assertEqual(response.data['likes_count'], 1)
        # user_a self likes the tweet
        self.user_a_client.post(LIKE_BASE_URL, data)
        # user_b get newsfeed
        response = self.user_b_client.get(NEWSFEED_LIST_API)
        self.assertEqual(response.status_code, 200)
        print(response.data)

        self.create_newsfeed(self.user_b, tweet)
        response = self.user_b_client.get(NEWSFEED_LIST_API)
        print(response.data)

