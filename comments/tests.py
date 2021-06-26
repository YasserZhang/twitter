

# Create your tests here.
from testing.testcases import TestCase


class CommentModelTests(TestCase):

    def setUp(self):
        super().setUp()
        self.tweet = self.create_tweet(self.user_a)
        self.comment = self.create_comment(self.user_a, self.tweet)

    def test_comment(self):
        self.assertNotEqual(self.comment.__str__(), None)

    def test_like_set(self):
        self.create_like(self.user_a, self.comment)
        self.assertEqual(self.comment.like_set.count(), 1)

        self.create_like(self.user_a, self.comment)
        self.assertEqual(self.comment.like_set.count(), 1)

        self.create_like(self.user_b, self.comment)
        self.assertEqual(self.comment.like_set.count(), 2)