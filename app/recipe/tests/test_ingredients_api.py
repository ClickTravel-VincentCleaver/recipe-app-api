from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient

from recipe.serializers import IngredientSerializer


INGREDIENTS_URL = reverse('recipe:ingredient-list')


class PublicIngredientsApiTests(TestCase):
    """Test publicly available ingredients API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that authentication is required to retrieve ingredients"""
        response = self.client.get(INGREDIENTS_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTests(TestCase):
    """Test private ingredients API"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'random@random.com',
            'MOCK_PASSWORD'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredient_list(self):
        """Test retrieve list of ingredients"""

        # Given existing ingredients
        Ingredient.objects.create(user=self.user, name='Pomegranite')
        Ingredient.objects.create(user=self.user, name='Aubergine')

        # When
        response = self.client.get(INGREDIENTS_URL)

        # Then the response is successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Then the response contains the ingredients
        expected_ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(expected_ingredients, many=True)
        expected_data = serializer.data
        self.assertEqual(response.data, expected_data)

    def test_retrieve_ingredients_list_for_user(self):
        """Test that ingredients for the authed user are returned"""

        # Given the user has an ingredient
        my_ingredient = Ingredient.objects.create(user=self.user, name='Grape')

        # Given another user also has an ingredient
        other_user = get_user_model().objects.create_user(
            'other@random.com',
            'other password'
        )
        Ingredient.objects.create(user=other_user, name='Tomato')

        # When
        response = self.client.get(INGREDIENTS_URL)

        # Then the response is successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Then the response contains only my ingredient
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], my_ingredient.name)

    def test_create_ingredient_successful(self):
        """Test create a new ingredient"""

        # Given
        payload = {'name': 'Broccoli'}

        # When
        self.client.post(INGREDIENTS_URL, payload)

        # Then
        exists = Ingredient.objects.filter(
            user=self.user,
            name=payload['name'],
        ).exists()
        self.assertTrue(exists)

    def test_create_ingredient_invalid(self):
        """Test create ingredient with invalid payload"""

        # Given
        payload = {'name': ''}

        # When
        response = self.client.post(INGREDIENTS_URL, payload)

        # Then
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
