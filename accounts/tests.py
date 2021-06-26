

# Create your tests here.

from accounts.models import UserProfile
from testing.testcases import TestCase


class UserProfileTest(TestCase):

    def setUp(self):
        super().setUp()
        self.clear_cache()

    def test_profile_property(self):
        self.assertEqual(UserProfile.objects.count(), 0)
        p = self.user_a.profile
        self.assertEqual(isinstance(p, UserProfile), True)
        self.assertEqual(UserProfile.objects.count(), 1)