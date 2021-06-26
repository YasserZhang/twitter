from friendships.models import Friendship
from friendships.services import FriendshipService
from testing.testcases import TestCase

# Create your tests here.

class FriendshipServiceTests(TestCase):

    def test_get_followings(self):
        user_c = self.create_user('user_c')
        user_d = self.create_user('user_d')
        for to_user in [user_c, user_d, self.user_b]:
            Friendship.objects.create(from_user=self.user_a, to_user=to_user)
        FriendshipService.invalidate_following_cache(self.user_a)

        user_id_set = FriendshipService.get_following_user_id_set(self.user_a)
        self.assertEqual(user_id_set, {user_c.id, user_d.id, self.user_b.id})

        Friendship.objects.filter(from_user=self.user_a, to_user=self.user_b).delete()
        FriendshipService.invalidate_following_cache(self.user_a)
        user_id_set = FriendshipService.get_following_user_id_set(self.user_a.id)
        self.assertSetEqual(user_id_set, {user_c.id, user_d.id})
