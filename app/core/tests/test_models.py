from django.test import TestCase
from django.contrib.auth import get_user_model
from core import models


def sample_user(email='random@random.com', password='Password1'):
    """Create a sample user"""
    return get_user_model().objects.create_user(email, password)


class ModelTests(TestCase):

    def test_create_user_with_email_successful(self):
        """Test creation of new user with email is successful"""

        # Given
        email = 'random@random.com'
        password = 'Password1'

        # When
        user = get_user_model().objects.create_user(
           email=email,
           password=password
        )

        # Then
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_create_user_email_normalised(self):
        """Test the email for a new user is normalised"""

        # Given
        email = 'ranDoM@DoMaIn.CoM'
        password = 'MOCK_PASSWORD'

        # When
        user = get_user_model().objects.create_user(email, password)

        # Then
        self.assertEqual(user.email, 'ranDoM@domain.com')

    def test_create_user_invalid_email(self):
        """Test that creating user with no email raises error"""

        # Given
        email = None
        password = 'MOCK_PASSWORD'

        # When / Then
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(email, password)

    def test_create_superuser(self):
        """Test creation of new superuser"""

        # Given
        email = 'random@random.com'
        password = 'MOCK_PASSWORD'

        # When
        user = get_user_model().objects.create_superuser(email, password)

        # Then
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_tag_str(self):
        """Test the tag string representation"""
        tag = models.Tag.objects.create(
            user=sample_user(),
            name='Dessert'
        )

        self.assertEqual(str(tag), tag.name)
