import tempfile
import os

from PIL import Image

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer


RECIPES_URL = reverse('recipe:recipe-list')


def image_upload_url(recipe_id):
    """Return recipe image upload URL"""
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


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

    def test_create_recipe(self):
        """Test creating a basic recipe"""

        # Given
        payload = {
            'title': 'Chocolate Cheesecake',
            'time_minutes': 30,
            'price': 5.00
        }

        # When
        response = self.client.post(RECIPES_URL, payload)

        # Then the response is successful
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Then the recipe is created
        recipe = Recipe.objects.get(id=response.data['id'])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_create_recipe_with_tags(self):
        """Test creating a recipe with tags"""

        # Given
        tag1 = sample_tag(user=self.user, name='Vegetarian')
        tag2 = sample_tag(user=self.user, name='Breakfast')
        payload = {
            'title': 'Big Breakfast',
            'tags': [tag1.id, tag2.id],
            'time_minutes': 20,
            'price': 10.00
        }

        # When
        response = self.client.post(RECIPES_URL, payload)

        # Then the response is successful
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Then the recipe is created with the tags
        recipe = Recipe.objects.get(id=response.data['id'])
        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_create_recipe_with_ingredients(self):
        """Test creating a recipe with ingredients"""

        # Given
        ingredient1 = sample_ingredient(user=self.user, name='Eggs')
        ingredient2 = sample_ingredient(user=self.user, name='Butter')
        payload = {
            'title': 'Scrambled Eggs',
            'ingredients': [ingredient1.id, ingredient2.id],
            'time_minutes': 5,
            'price': 2.00
        }

        # When
        response = self.client.post(RECIPES_URL, payload)

        # Then the response is successful
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Then the recipe is created with the ingredients
        recipe = Recipe.objects.get(id=response.data['id'])
        ingredients = recipe.ingredients.all()
        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient1, ingredients)
        self.assertIn(ingredient2, ingredients)

    def test_partial_update_recipe(self):
        """Test updating a recipe with PATCH"""

        # Given
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))

        new_tag = sample_tag(user=self.user, name='Soup')
        payload = {
            'title': 'Chicken Soup',
            'tags': [new_tag.id]
        }

        # When
        url = recipe_detail_url(recipe.id)
        self.client.patch(url, payload)

        # Then
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        tags = recipe.tags.all()
        self.assertEqual(len(tags), 1)
        self.assertIn(new_tag, tags)

    def test_full_update_recipe(self):
        """Test updating a recipe with PUT"""

        # Given
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))

        payload = {
            'title': 'Minestrone Soup',
            'time_minutes': 25,
            'price': 5.00
        }

        # When
        url = recipe_detail_url(recipe.id)
        self.client.put(url, payload)

        # Then
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.time_minutes, payload['time_minutes'])
        self.assertEqual(recipe.price, payload['price'])
        tags = recipe.tags.all()
        self.assertEqual(len(tags), 0)


class RecipeImageUploadTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'random@random.com',
            'MOCK_PASSWORD'
        )
        self.client.force_authenticate(self.user)
        self.recipe = sample_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image_to_recipe(self):
        """Test uploading image to recipe"""

        # Given
        url = image_upload_url(self.recipe.id)

        # When
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            img = Image.new('RGB', (8, 8))
            img.save(ntf, format='JPEG')
            ntf.seek(0)
            response = self.client.post(
                url,
                {'image': ntf},
                format='multipart'
            )

        # Then
        self.recipe.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('image', response.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading invalid image"""

        # Given
        url = image_upload_url(self.recipe.id)

        # When
        response = self.client.post(
            url,
            {'image': 'NOT_AN_IMAGE!'},
            format='multipart'
        )

        # Then
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
