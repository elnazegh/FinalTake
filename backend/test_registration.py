import unittest
from unittest.mock import patch, MagicMock

from app import app


class RegistrationApiTests(unittest.TestCase):

    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    @patch("app.get_db_connection")
    def test_successful_registration(self, mock_get_db_connection):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()

        mock_get_db_connection.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor

        mock_cursor.fetchone.return_value = None

        response = self.client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "password123"
            }
        )

        self.assertEqual(response.status_code, 201)

    def test_missing_username(self):
        response = self.client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "password123"
            }
        )

        self.assertEqual(response.status_code, 400)

    def test_missing_email(self):
        response = self.client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "password": "password123"
            }
        )

        self.assertEqual(response.status_code, 400)

    def test_missing_password(self):
        response = self.client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com"
            }
        )

        self.assertEqual(response.status_code, 400)

    @patch("app.get_db_connection")
    def test_duplicate_user(self, mock_get_db_connection):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()

        mock_get_db_connection.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor

        mock_cursor.execute.side_effect = Exception("Duplicate entry")

        response = self.client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "password123"
            }
        )

        self.assertEqual(response.status_code, 409)

    @patch("app.get_db_connection")
    def test_password_is_hashed(self, mock_get_db_connection):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()

        mock_get_db_connection.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor

        response = self.client.post(
            "/api/auth/register",
            json={
                "username": "secureuser",
                "email": "secure@example.com",
                "password": "password123"
            }
        )

        self.assertEqual(response.status_code, 201)

        args, _ = mock_cursor.execute.call_args
        parameters = args[1]

        stored_password = parameters[2]

        self.assertNotEqual(stored_password, "password123")
        self.assertTrue(len(stored_password) > 20)

    def test_invalid_email_format(self):
        response = self.client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "email": "not-an-email",
                "password": "password123"
            }
        )

        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()