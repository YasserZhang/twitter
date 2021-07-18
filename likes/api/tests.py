from rest_framework.test import APIClient

from friendships.models import Friendship
from testing.testcases import TestCase

LIKE_BASE_URL='/api/likes/'
LIKE_CANCEL_URL = '/api/likes/cancel/'
COMMENT_LIST_API = '/api/comments/'
TWEET_LIST_API = '/api/tweets/'
TWEET_DETAIL_API = '/api/tweets/{}/'
TWEET_DETAIL_WITH_ALL_COMMENTS_API = '/api/tweets/{}/?with_all_comments'
NEWSFEED_LIST_API = '/api/newsfeeds/'
FOLLOW_URL = '/api/friendships/{}/follow/'
FOLLOWERS_URL = '/api/friendships/{}/followers/'


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

    def test_comments_count(self):
        # test tweet detail api
        tweet = self.create_tweet(self.user_a)
        url = TWEET_DETAIL_WITH_ALL_COMMENTS_API.format(tweet.id)
        response = self.user_b_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['comments_count'], 0)

        # test tweet list api
        self.create_comment(self.user_a, tweet.id)
        response = self.user_b_client.get(TWEET_LIST_API, {'user_id': self.user_a.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['comments_count'], 1)

        # test newsfeeds list api
        self.create_comment(self.user_b, tweet.id)
        self.create_newsfeed(self.user_b, tweet)
        response = self.user_b_client.get(NEWSFEED_LIST_API)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['tweet']['comments_count'], 2)

    def test_likes_in_tweets_api(self):
        # user_b follows user_a
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
        response = self.user_a_client.get(TWEET_LIST_API, {'user_id': self.user_a.id})
        self.assertEqual(response.data['results'][0]['has_liked'], True)
        self.assertEqual(response.data['results'][0]['likes_count'], 2)

        # user_b get newsfeed
        response = self.user_b_client.get(NEWSFEED_LIST_API)
        self.assertEqual(response.status_code, 200)
        print(response.data)
        self.assertEqual(response.data['results'][0]['tweet']['has_liked'], True)
        self.assertEqual(response.data['results'][0]['tweet']['likes_count'], 2)

    def test_likes_in_comments_api(self):
        tweet = self.create_tweet(self.user_a)
        comment = self.create_comment(self.user_b, tweet.id)

        # test anonymous
        anonymous_client = APIClient()
        response = anonymous_client.get(COMMENT_LIST_API, {'tweet_id': tweet.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['comments'][0]['has_liked'], False)
        self.assertEqual(response.data['comments'][0]['likes_count'], 0)

        # test comments list api
        response = self.user_b_client.get(COMMENT_LIST_API, {'tweet_id': tweet.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['comments'][0]['has_liked'], False)
        self.assertEqual(response.data['comments'][0]['likes_count'], 0)
        self.create_like(self.user_b, comment)
        response = self.user_b_client.get(COMMENT_LIST_API, {'tweet_id': tweet.id})
        self.assertEqual(response.data['comments'][0]['has_liked'], True)
        self.assertEqual(response.data['comments'][0]['likes_count'], 1)

        # test tweet detail api
        self.create_like(self.user_a, comment)
        url = TWEET_DETAIL_WITH_ALL_COMMENTS_API.format(tweet.id)
        response = self.user_b_client.get(url)
        self.assertEqual(response.status_code, 200)
        print("response:", response.data)
        self.assertEqual(response.data['comments'][0]['has_liked'], True)
        self.assertEqual(response.data['comments'][0]['likes_count'], 2)

    def test_likes_count(self):
        tweet = self.create_tweet(self.user_a)
        data = {'content_type': 'tweet', 'object_id': tweet.id}
        self.user_b_client.post(LIKE_BASE_URL, data)

        tweet_url = TWEET_DETAIL_API.format(tweet.id)
        response = self.user_a_client.get(tweet_url)
        self.assertEqual(response.data['likes_count'], 1)
        tweet.refresh_from_db()
        self.assertEqual(tweet.likes_count, 1)

        self.user_b_client.post(LIKE_CANCEL_URL, data)
        tweet.refresh_from_db()
        self.assertEqual(tweet.likes_count, 0)
        response = self.user_a_client.get(tweet_url)
        self.assertEqual(response.data['likes_count'], 0)