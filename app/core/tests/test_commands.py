from unittest.mock import patch

from django.core.management import call_command
from django.db.utils import OperationalError
from django.test import TestCase


class CommandTests(TestCase):

    def test_wait_for_db_ready(self):
        """Test waiting for db when db is available"""

        # Given
        with patch('django.db.utils.ConnectionHandler.__getitem__') \
                as mock_get_item:
            mock_get_item.return_value = True

            # When
            call_command('wait_for_db')

            # Then
            self.assertEqual(mock_get_item.call_count, 1)

    @patch('time.sleep', return_value=True)
    def test_wait_for_db(self, mock_time_sleep):
        """Test waiting for db"""

        # Given
        with patch('django.db.utils.ConnectionHandler.__getitem__') \
                as mock_get_item:
            mock_get_item.side_effect = [OperationalError] * 5 + [True]

            # When
            call_command('wait_for_db')

            # Then
            self.assertEqual(mock_get_item.call_count, 6)
