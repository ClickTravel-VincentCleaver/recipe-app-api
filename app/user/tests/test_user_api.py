from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """Test the users API (public)"""

    # ------------------------------------------------------
    # CREATE USER tests
    # ------------------------------------------------------

    def setUp(self):
        self.client = APIClient()

    def test_create_user_success(self):
        """Test that create user with valid payload is successful"""

        # Given
        payload = {
            'email': 'random@random.com',
            'password': 'MOCK_PASSWORD',
            'name': 'MOCK_NAME'
        }

        # When
        response = self.client.post(CREATE_USER_URL, payload)

        # Then a success response status is returned
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Then the password is stored for the user
        user = get_user_model().objects.get(**response.data)
        self.assertTrue(user.check_password(payload['password']))

        # Then the password is not returned in the response
        self.assertNotIn('password', response.data)

    def test_create_duplicate_user_fails(self):
        """Test creating a user that already exists fails"""

        # Given a user that already exists
        payload = {
            'email': 'random@random.com',
            'password': 'MOCK_PASSWORD',
            'name': 'MOCK_NAME'
        }
        create_user(**payload)

        # When
        response = self.client.post(CREATE_USER_URL, payload)

        # Then a bad request status is returned
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_with_password_too_short(self):
        """Test creating a user with a password
         that is not more than 5 characters"""

        # Given a create user request with a too-short password
        payload = {
            'email': 'random@random.com',
            'password': '1234',
            'name': 'MOCK_NAME'
        }

        # When
        response = self.client.post(CREATE_USER_URL, payload)

        # Then a bad request status is returned
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Then the user is not created
        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exists)

    # ------------------------------------------------------
    # TOKEN tests
    # ------------------------------------------------------

    def test_create_token_for_user(self):
        """Test that a token is created for the user"""

        # Given
        payload = {'email': 'random@random.com', 'password': 'MOCK_PASSWORD'}
        create_user(**payload)

        # When
        response = self.client.post(TOKEN_URL, payload)

        # Then the response is successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Then the response contains a token
        self.assertIn('token', response.data)

    def test_create_token_invalid_credentials(self):
        """Test that token is not created for invalid credentials"""

        # Given
        create_user(email='random@random.com', password='MOCK_PASSWORD')
        payload = {
            'email': 'random@random.com',
            'password': 'MOCK_INVALID_PASSWORD'
        }

        # When
        response = self.client.post(TOKEN_URL, payload)

        # Then the response fails
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Then the response does not contain a token
        self.assertNotIn('token', response.data)

    def test_create_token_no_user(self):
        """Test that token is not created for non-existent user"""

        # Given
        payload = {'email': 'random@random.com', 'password': 'MOCK_PASSWORD'}

        # When
        response = self.client.post(TOKEN_URL, payload)

        # Then the response fails
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Then the response does not contain a token
        self.assertNotIn('token', response.data)

    def test_create_token_missing_password(self):
        """Test that email and password are required"""

        # Given
        create_user(email='random@random.com', password='MOCK_PASSWORD')
        payload = {'email': 'random@random.com', 'password': ''}

        # When
        response = self.client.post(TOKEN_URL, payload)

        # Then the response fails
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Then the response does not contain a token
        self.assertNotIn('token', response.data)

    # ------------------------------------------------------
    # ME tests
    # ------------------------------------------------------

    def test_get_me_unauthorised(self):
        """Test that authentication is required for users"""

        # Given no authentication token

        # When
        response = self.client.get(ME_URL)

        # Then
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    """Test API requests that require authentication"""

    def setUp(self):
        self.user = create_user(
            email='random@random.com',
            password='MOCK_PASSWORD',
            name='MOCK_NAME'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_get_me_success(self):
        """Test get me for authenticated user"""
        response = self.client.get(ME_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {
                'name': self.user.name,
                'email': self.user.email
            },
        )

    def test_post_me_not_allowed(self):
        """Test that POST is not allowed on me URL"""

        # Given / When
        response = self.client.post(ME_URL, {})

        # Then
        self.assertEqual(
            response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_me_success(self):
        """Test updating the user profile for authenticated user"""

        # Given
        payload = {
            'name': 'MOCK_NEW_NAME',
            'password': 'MOCK_NEW_PASSWORD',
        }

        # When
        response = self.client.patch(ME_URL, payload)

        # Then request is successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Then user is updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
