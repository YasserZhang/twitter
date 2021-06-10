from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from testing.testcases import TestCase

LOGIN_URL = '/api/accounts/login/'
LOGIN_STATUS_URL = '/api/accounts/login_status/'
LOGOUT_URL = '/api/accounts/logout/'
SIGNUP_URL = '/api/accounts/signup/'
USER_PROFILE_DETAIL_URL = '/api/profiles/{}/'

def create_user(username, email, password):
    return User.objects.create_user(username, email, password)


class AccountApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            username='admin',
            email='admin@jiuzhang.com',
            password='correct password',
        )

    def test_login(self):
        # login using get instead of post
        response = self.client.get(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correct password',
        })
        self.assertEqual(response.status_code, 405)

        # wrong password
        response = self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'wrong password',
        })
        self.assertEqual(response.status_code, 400)

        # not logged in
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], False)

        # login success
        response = self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correct password',
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.data['user'], None)
        self.assertEqual(response.data['user']['email'], 'admin@jiuzhang.com')

        # logged in
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)

    def test_logout(self):
        self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correct password',
        })

        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)

        response = self.client.get(LOGOUT_URL)
        self.assertEqual(response.status_code, 405)

        response = self.client.post(LOGOUT_URL)
        self.assertEqual(response.status_code, 200)

        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], False)

    def test_signup(self):
        data = {
            'username': 'someone',
            'email': 'someone@jiuzhang.com',
            'password': 'any password',
        }

        # wrong http method, GET instead of POST
        response = self.client.get(SIGNUP_URL, data)
        self.assertEqual(response.status_code, 405)

        #invalid email format
        response = self.client.post(SIGNUP_URL, {
            'username': 'someone',
            'email': 'not a correct email',
            'password': 'any password',
        })
        self.assertEqual(response.status_code, 400)

        # password too short
        response = self.client.post(SIGNUP_URL, {
            'username': 'someone',
            'email': 'someone@jiuzhang.com',
            'password': '123',
        })
        self.assertEqual(response.status_code, 400)

        # username too long
        response = self.client.post(SIGNUP_URL, {
            'username': 'username is tooooooooooooooooo loooooooong',
            'email': 'someone@jiuzhang.com',
            'password': 'any password',
        })
        self.assertEqual(response.status_code, 400)

        # signup success
        response = self.client.post(SIGNUP_URL, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['username'], 'someone')
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)


class UserProfileAPITests(TestCase):

    def test_update(self):
        p = self.user_a.profile
        p.nickname = 'old nickname'
        p.save()
        url = USER_PROFILE_DETAIL_URL.format(p.id)

        # other client not allowed to update your user profile
        response = self.user_b_client.put(url, {
            'nickname': 'new nickname',
        })
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['detail'], 'You do not have permission to access this object')
        p.refresh_from_db()
        self.assertEqual(p.nickname, 'old nickname')

        # update user profile successfully
        response = self.user_a_client.put(url, {
            'nickname': 'new nickname',
        })
        self.assertEqual(response.status_code, 200)
        p.refresh_from_db()
        self.assertEqual(p.nickname, 'new nickname')

        # update avatar
        response = self.user_a_client.put(url, {
            'avatar': SimpleUploadedFile(
                name='my-avatar.jpg',
                content=str.encode('a fake image'),
                content_type = 'image/jpeg',
            ),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual('my-avatar' in response.data['avatar'], True)
        p.refresh_from_db()
        self.assertIsNotNone(p.avatar)
