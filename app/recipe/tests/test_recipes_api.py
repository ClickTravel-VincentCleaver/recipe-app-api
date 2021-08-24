from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer


RECIPES_URL = reverse('recipe:recipe-list')


def recipe_detail_url(recipe_id):
    """Return recipe detail URL"""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def sample_tag(user, name='Main course'):
    """Create and return a sample tag"""
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name='Flour'):
    """Create and return a sample ingredient"""
    return Ingredient.objects.create(user=user, name=name)


def sample_recipe(user, **params):
    """Create and return a sample recipe"""
    defaults = {
        'title': 'Sample Recipe',
        'time_minutes': 10,
        'price': 5.00
    }
    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeApiTests(TestCase):
    """Test unauthenticated receipAPI access"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test that authentication is required"""
        # response = self.client.get(RECIPES_URL)
        # self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """Test private recipe API"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'random@random.com',
            'MOCK_PASSWORD'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes_list(self):
        """Test retrieving list of recipes"""

        # Given
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)

        # When
        response = self.client.get(RECIPES_URL)

        # Then the response is successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Then the response contains the recipes
        expected_recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(expected_recipes, many=True)
        expected_data = serializer.data
        self.assertEqual(response.data, expected_data)

    def test_recipes_limited_to_user(self):
        """Test retrieving recipes for user"""

        # Given
        other_user = get_user_model().objects.create_user(
            'other@random.com',
            'OTHER_PASSWORD'
        )
        sample_recipe(user=other_user)
        sample_recipe(user=self.user)

        # When
        response = self.client.get(RECIPES_URL)

        # Then the response is successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Then only my recipe is returned
        expected_recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(expected_recipes, many=True)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data, serializer.data)

    def test_view_recipe_detail(self):
        """Test viewing a recipe detail"""

        # Given
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))

        # When
        url = recipe_detail_url(recipe.id)
        response = self.client.get(url)

        # Then the response is successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Then the recipe is returned
        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(response.data, serializer.data)
