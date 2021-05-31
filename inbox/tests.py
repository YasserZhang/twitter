from notifications.models import Notification

from inbox.services import NotificationService
from testing.testcases import TestCase


class NotificationServiceTests(TestCase):

    def setUp(self):
        super().setUp()
        self.tweet = self.create_tweet(self.user_a)

    def test_send_comment_notification(self):
        # do not dispatch notification if tweet user == comment user
        comment = self.create_comment(self.user_a, self.tweet.id)
        NotificationService.send_comment_notification(comment)
        self.assertEqual(Notification.objects.count(), 0)

        # dispatch notifications if tweet user != comment user
        comment = self.create_comment(self.user_b, self.tweet.id)
        NotificationService.send_comment_notification(comment)
        self.assertEqual(Notification.objects.count(), 1)

    def test_send_like_notifications(self):
        # do not dispatch notification if tweet user == like user
        like = self.create_like(self.user_a, self.tweet)
        NotificationService.send_like_notification(like)
        self.assertEqual(Notification.objects.count(), 0)

        # dispatch notification if tweet user != like user
        like = self.create_like(self.user_b, self.tweet)
        NotificationService.send_like_notification(like)
        self.assertEqual(Notification.objects.count(), 1)