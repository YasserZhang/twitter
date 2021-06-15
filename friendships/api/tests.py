from rest_framework.test import APIClient

from friendships.models import Friendship
from testing.testcases import TestCase

FOLLOW_URL = '/api/friendships/{}/follow/'
UNFOLLOW_URL = '/api/friendships/{}/unfollow/'
FOLLOWERS_URL = '/api/friendships/{}/followers/'
FOLLOWINGS_URL = '/api/friendships/{}/followings/'


class FriendshipTestCase(TestCase):

    def setUp(self):
        self.clear_cache()
        self.anonymous_client = APIClient()
        self.user_a = self.create_user('user_a')
        self.user_a_client = APIClient()
        self.user_a_client.force_authenticate(self.user_a)

        self.user_b = self.create_user('user_b')
        self.user_b_client = APIClient()
        self.user_b_client.force_authenticate(self.user_b)

        for i in range(2):
            follower = self.create_user('user_a_follower{}'.format(i))
            Friendship.objects.create(from_user=follower, to_user=self.user_a)

        for i in range(3):
            following = self.create_user('user_b_following{}'.format(i))
            Friendship.objects.create(from_user=self.user_b, to_user=following)

    def test_follow(self):
        url = FOLLOW_URL.format(self.user_a.id)
        # unauthenticated follow
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 403)

        # get follow url, throw 405
        response = self.user_a_client.get(url)
        self.assertEqual(response.status_code, 405)

        # follow self
        response = self.user_a_client.post(url)
        self.assertEqual(response.status_code, 400)

        # follow successfully
        response = self.user_b_client.post(url)
        self.assertEqual(response.status_code, 201)

        # follow the same user again
        response = self.user_b_client.post(url)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['duplicate'], True)

        # follow back
        count = Friendship.objects.count()
        response = self.user_a_client.post(FOLLOW_URL.format(self.user_b.id))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Friendship.objects.count(), count+1)

    def test_unfollow(self):
        url = UNFOLLOW_URL.format(self.user_a.id)

        # unauthenticated unfollow
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 403)

        # get unfollow, get 405
        response = self.user_b_client.get(url)
        self.assertEqual(response.status_code, 405)

        # unfollow self
        response = self.user_a_client.post(url)
        self.assertEqual(response.status_code, 400)

        # unfollow successfully
        Friendship.objects.create(from_user=self.user_b, to_user=self.user_a)
        count = Friendship.objects.count()
        response = self.user_b_client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 1)
        self.assertEqual(Friendship.objects.count(), count - 1)

        # do nothing when no follow
        count = Friendship.objects.count()
        response = self.user_b_client.post(url)
        self.assertEqual(response.data['deleted'], 0)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Friendship.objects.count(), count)

    def test_followings(self):
        url = FOLLOWINGS_URL.format(self.user_b.id)

        # unauthenticated call
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['followings']), 3)

        # followings are listed by created_at
        ts0 = response.data['followings'][0]['created_at']
        ts1 = response.data['followings'][1]['created_at']
        ts2 = response.data['followings'][2]['created_at']
        self.assertEqual(ts0 > ts1, True)
        self.assertEqual(ts1 > ts2, True)
        self.assertEqual(
            response.data['followings'][0]['user']['username'],
            'user_b_following2'
        )
        self.assertEqual(
            response.data['followings'][1]['user']['username'],
            'user_b_following1'
        )
        self.assertEqual(
            response.data['followings'][2]['user']['username'],
            'user_b_following0'
        )

        # post is not allowed, get 405
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 405)

    def test_followers(self):
        url = FOLLOWERS_URL.format(self.user_a.id)

        # successfully get
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['followers']), 2)

        # followers are listed by created_at
        ts0 = response.data['followers'][0]['created_at']
        ts1 = response.data['followers'][1]['created_at']
        self.assertGreater(ts0, ts1, "ts0 should be greater than ts1")

        self.assertEqual(
            response.data['followers'][0]['user']['username'],
            'user_a_follower1'
        )
        self.assertEqual(
            response.data['followers'][1]['user']['username'],
            'user_a_follower0'
        )

        # post is not allowed, throw 405
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 405)