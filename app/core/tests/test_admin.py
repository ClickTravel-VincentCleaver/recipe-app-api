from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse


class AdminSiteTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            email='admin@random.com',
            password='Password1'
        )
        self.client.force_login(self.admin_user)
        self.user = get_user_model().objects.create_user(
            email='random@random.com',
            password='Password1',
            name='Test User full name'
        )

    def test_users_listed(self):
        """Test that users are listed on user page"""

        # Given
        url = reverse('admin:core_user_changelist')

        # When
        res = self.client.get(url)

        # Then
        self.assertContains(res, self.user.name)
        self.assertContains(res, self.user.email)

    def test_user_edit_page(self):
        """Test that the user edit page works"""

        # Given
        url = reverse('admin:core_user_change', args=[self.user.id])

        # When
        res = self.client.get(url)

        # Then
        self.assertEqual(res.status_code, 200)

    def test_user_add_page(self):
        """Test that the user create page works"""

        # Given
        url = reverse('admin:core_user_add')

        # When
        res = self.client.get(url)

        # Then
        self.assertEqual(res.status_code, 200)
