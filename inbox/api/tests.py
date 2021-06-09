from notifications.models import Notification

from testing.testcases import TestCase

COMMENT_URL = '/api/comments/'
LIKE_URL = '/api/likes/'
NOTIFICATION_URL = '/api/notifications/'
UNREAD_URL = '/api/notifications/unread-count/'
MARK_AS_READ_URL = '/api/notifications/mark-all-as-read/'
NOTIFICATION_UPDATE_URL = '/api/notifications/{}/'


class NotificationTests(TestCase):

    def setUp(self):
        super().setUp()
        self.tweet = self.create_tweet(self.user_a)

    def test_comment_create_api_trigger_notification(self):
        self.assertEqual(Notification.objects.count(), 0)
        self.user_b_client.post(COMMENT_URL, {
            'tweet_id': self.tweet.id,
            'content': 'a ha',
        })
        self.assertEqual(Notification.objects.count(), 1)

    def test_like_create_api_trigger_notification(self):
        self.assertEqual(Notification.objects.count(), 0)
        self.user_b_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': self.tweet.id,
        })
        self.assertEqual(Notification.objects.count(), 1)


class NotificationApiTest(TestCase):

    def setUp(self):
        super().setUp()
        self.tweet = self.create_tweet(self.user_a)

    def test_unread_count(self):
        self.user_b_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': self.tweet.id,
        })
        response = self.user_a_client.get(UNREAD_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['unread_count'], 1)

        comment = self.create_comment(self.user_a, self.tweet.id)
        self.user_b_client.post(LIKE_URL, {
            'content_type': 'comment',
            'object_id': comment.id,
        })
        response = self.user_a_client.get(UNREAD_URL)
        self.assertEqual(response.data['unread_count'], 2)

    def test_mark_all_as_read(self):
        self.user_b_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': self.tweet.id,
        })
        comment = self.create_comment(self.user_a, self.tweet.id)
        self.user_b_client.post(LIKE_URL, {
            'content_type': 'comment',
            'object_id': comment.id,
        })
        response = self.user_a_client.get(UNREAD_URL)
        self.assertEqual(response.data['unread_count'], 2)

        # GET not allowed
        response = self.user_a_client.get(MARK_AS_READ_URL)
        self.assertEqual(response.status_code, 405)

        response = self.user_a_client.post(MARK_AS_READ_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['marked_count'], 2)

        response = self.user_a_client.get(UNREAD_URL)
        self.assertEqual(response.data['unread_count'], 0)

    def test_list(self):
        self.user_b_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': self.tweet.id,
        })
        comment = self.create_comment(self.user_a, self.tweet.id)
        self.user_b_client.post(LIKE_URL, {
            'content_type': 'comment',
            'object_id': comment.id,
        })

        # anonymous get not allowed
        response = self.anonymous_client.get(NOTIFICATION_URL)
        self.assertEqual(response.status_code, 403)
        # user_b cannot see notifications
        response = self.user_b_client.get(NOTIFICATION_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)
        # user_a can see two notifications
        response = self.user_a_client.get(NOTIFICATION_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        # mark the first unread as read
        notification = self.user_a.notifications.first()
        notification.unread = False
        notification.save()
        notifications = self.user_a.notifications.all()
        for notification in notifications:
            print(notification.unread)
        # print("first notification: ", notification.unread)
        response = self.user_a_client.get(NOTIFICATION_URL)
        self.assertEqual(response.data['count'], 2)
        response = self.user_a_client.get(NOTIFICATION_URL, {'unread': True})
        self.assertEqual(response.data['count'], 1)
        response = self.user_a_client.get(NOTIFICATION_URL, {'unread': False})
        self.assertEqual(response.data['count'], 1)

    def test_update(self):
        self.user_b_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': self.tweet.id,
        })
        comment = self.create_comment(self.user_a, self.tweet.id)
        self.user_b_client.post(LIKE_URL, {
            'content_type': 'comment',
            'object_id': comment.id,
        })
        notification = self.user_a.notifications.first()
        url = NOTIFICATION_UPDATE_URL.format(notification.id)
        # post not allowed
        response = self.user_a_client.post(url, {'unread': False})
        self.assertEqual(response.status_code, 405)

        # other users not allowed to change notification status
        response = self.anonymous_client.put(url, {'unread': False})
        self.assertEqual(response.status_code, 403)
        # user_b doesn't have notification, return 404
        response = self.user_b_client.put(url, {'unread': False})
        self.assertEqual(response.status_code, 404)

        # successful update
        response = self.user_a_client.put(url, {'unread': False})
        self.assertEqual(response.status_code, 200)
        response = self.user_a_client.get(UNREAD_URL)
        self.assertEqual(response.data['unread_count'], 1)

        # mark it as unread again
        self.user_a_client.put(url, {'unread': True})
        response = self.user_a_client.get(UNREAD_URL)
        self.assertEqual(response.data['unread_count'], 2)
        # must have unread keyword in payload
        response = self.user_a_client.put(url, {'verb': 'wrong-verb'})
        self.assertEqual(response.status_code, 400)
        # must not update fields
        response = self.user_a_client.put(url, {'verb': 'newverb', 'unread': False})
        self.assertEqual(response.status_code, 200)
        notification.refresh_from_db()
        self.assertNotEqual(notification.verb, 'newverb')