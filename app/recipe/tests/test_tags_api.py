from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, Recipe

from recipe.serializers import TagSerializer


TAGS_URL = reverse('recipe:tag-list')


class PublicTagsApiTests(TestCase):
    """Test the publicly available Tags API"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test that authentication is required for retrieving tags"""
        response = self.client.get(TAGS_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):
    """Test the authorised user Tags API"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            'random@random.com',
            'Password1'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test retrieve tags"""

        # Given
        Tag.objects.create(user=self.user, name='Dessert')
        Tag.objects.create(user=self.user, name='Starter')

        # When
        response = self.client.get(TAGS_URL)

        # Then the request is successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Then the tags are returned
        expected_tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(expected_tags, many=True)
        expected_data = serializer.data
        self.assertEqual(response.data, expected_data)

    def test_retrieve_tags_only_for_user(self):
        """Test retrieve on tags for authenticated user only"""

        # Given authenticated user has a tag
        expected_tag = Tag.objects.create(user=self.user, name='Dairy Free')

        # Given another user also has a tag
        other_user = get_user_model().objects.create_user(
            'other_user@random.com',
            'MOCK_OTHER_PASSWORD'
        )
        Tag.objects.create(user=other_user, name='MOCK_OTHER_TAG_NAME')

        # When
        response = self.client.get(TAGS_URL)

        # Then the request is successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Then only the tags belonging to the auth'd user are returned
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], expected_tag.name)

    def test_create_tag_success(self):
        """Test create a new tag"""

        # Given
        payload = {'name': 'TAG_NAME'}

        # When
        self.client.post(TAGS_URL, payload)

        # Then
        exists = Tag.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()
        self.assertTrue(exists)

    def test_create_tag_invalid_name_failure(self):
        """Test creating a tag with invalid payload"""

        # Given
        payload = {'name': ''}

        # When
        response = self.client.post(TAGS_URL, payload)

        # Then
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_tags_assigned_to_recipes(self):
        """Test filtering tags by those assigned to recipes"""

        # Given
        tag1 = Tag.objects.create(user=self.user, name='Breakfast')
        tag2 = Tag.objects.create(user=self.user, name='Lunch')
        recipe = Recipe.objects.create(
            title='Eggs Benedict',
            time_minutes=10,
            price=4.00,
            user=self.user
        )
        recipe.tags.add(tag1)

        # When
        response = self.client.get(TAGS_URL, {'assigned_only': 1})

        # Then
        serializer1 = TagSerializer(tag1)
        serializer2 = TagSerializer(tag2)
        self.assertIn(serializer1.data, response.data)
        self.assertNotIn(serializer2.data, response.data)

    def test_retrieve_tags_assigned_unique(self):
        """Test filtering tags by assigned returns unique items"""

        # Given
        tag = Tag.objects.create(user=self.user, name='Breakfast')
        Tag.objects.create(user=self.user, name='Lunch')
        recipe1 = Recipe.objects.create(
            title='Drop scones',
            time_minutes=15,
            price=2.50,
            user=self.user
        )
        recipe1.tags.add(tag)
        recipe2 = Recipe.objects.create(
            title='Porridge',
            time_minutes=5,
            price=1.50,
            user=self.user
        )
        recipe2.tags.add(tag)

        # When
        response = self.client.get(TAGS_URL, {'assigned_only': 1})

        # Then
        self.assertEqual(len(response.data), 1)
