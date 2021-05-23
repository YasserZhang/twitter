from django.utils import timezone

from comments.models import Comment
from testing.testcases import TestCase

COMMENT_URL = '/api/comments/'
TWEET_URL = '/api/tweets/'


class CommentTestCase(TestCase):

    def setUp(self):
        super().setUp()
        self.tweet = self.create_tweet(self.user_a)


    def test_create(self):
        tweet = self.create_tweet(self.user_a)
        # anonymous user creates a comment not allowed
        response = self.anonymous_client.post(COMMENT_URL)
        self.assertEqual(response.status_code, 403)

        # post comment without payload not allowed
        response = self.user_b_client.post(COMMENT_URL)
        self.assertEqual(response.status_code, 400)

        # post with a partially complete payload not allowed
        response = self.user_b_client.post(
            COMMENT_URL,
            {'tweet_id': tweet.id}
        )
        self.assertEqual(response.status_code, 400)

        # post without tweet id not allowed
        response = self.user_b_client.post(
            COMMENT_URL,
            {'content': 'test comment'}
        )
        self.assertEqual(response.status_code, 400)

        # content too long
        response = self.user_b_client.post(
            COMMENT_URL,
            {
                'tweet_id': tweet.id,
                'content': '1'*141,
            }
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['errors']['content'][0], 'Ensure this field has no more than 140 characters.')

        response = self.user_b_client.post(
            COMMENT_URL,
            {
                'tweet_id': tweet.id,
                'content': 'test comment',
            }
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['id'], self.user_b.id)
        self.assertEqual(response.data['tweet_id'], tweet.id)
        self.assertEqual(response.data['content'], 'test comment')

    def test_update(self):
        tweet = self.create_tweet(self.user_a)
        comment = self.create_comment(self.user_b, tweet.id)
        url = '{}{}/'.format(COMMENT_URL, comment.id)

        response = self.anonymous_client.put(url, {'content': 'new'})
        self.assertEqual(response.status_code, 403)

        response = self.user_a_client.put(url, {'content': 'new'})
        self.assertEqual(response.status_code, 403)

        comment.refresh_from_db()
        self.assertNotEqual(comment.content, 'new')

        # only content will be updated
        before_updated_at = comment.updated_at
        before_created_at = comment.created_at
        now = timezone.now()
        response = self.user_b_client.put(url, {
            'content': 'new',
            'user_id': self.user_a.id,
            'tweet_id': 123,
            'created_at': now,
        })
        self.assertEqual(response.status_code, 200)
        comment.refresh_from_db()
        self.assertEqual(comment.content, 'new')
        self.assertEqual(comment.user, self.user_b)
        self.assertEqual(comment.tweet, tweet)
        self.assertEqual(comment.created_at, before_created_at)
        self.assertNotEqual(comment.created_at, now)
        self.assertNotEqual(comment.updated_at, before_updated_at)

    def test_destroy(self):
        tweet = self.create_tweet(self.user_a)
        comment = self.create_comment(self.user_b, tweet.id)
        url = '{}{}/'.format(COMMENT_URL, comment.id)

        response = self.anonymous_client.delete(url)
        self.assertEqual(response.status_code, 403)

        response = self.user_a_client.delete(url)
        self.assertEqual(response.status_code, 403)

        count = Comment.objects.count()
        response = self.user_b_client.delete(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.count(), count-1)

    def test_list(self):
        comment1 = self.create_comment(self.user_b, self.tweet.id, '1')
        comment2 = self.create_comment(self.user_b, self.tweet.id, '2')
        response = self.anonymous_client.get(COMMENT_URL, {
            'tweet_id': self.tweet.id,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['comments']), 2)
        self.assertEqual(response.data['comments'][0]['content'], '1')
        self.assertEqual(response.data['comments'][1]['content'], '2')

        response = self.anonymous_client.get(COMMENT_URL, {
            'tweet_id': self.tweet.id,
            'user_id': self.user_a.id,
        })
        self.assertEqual(len(response.data['comments']), 2)
