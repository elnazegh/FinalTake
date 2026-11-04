
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from werkzeug.security import check_password_hash
from app import app


class PasswordRecoveryApiTests(unittest.TestCase):

    def setUp(self):
        app.config.update(
            TESTING=True,
            SECRET_KEY="testing-only-key"
        )

        self.client = app.test_client()

    def tearDown(self):
        with self.client.session_transaction() as sess:
            sess.clear()

    # Test 1: Missing email
    def test_forgot_password_missing_email(self):
        response = self.client.post(
            "/api/auth/forgot-password",
            json={}
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json["error"],
            "Email is required"
        )

    # Test 2: Valid password-reset request
    @patch("app.send_password_reset_email")
    @patch("app.get_db_connection")
    def test_forgot_password_valid_email(self, mock_db, mock_email):
        cursor = MagicMock()
        cursor.fetchone.return_value = {
            "user_id": 17,
            "email": "student@example.com"
        }

        mock_db.return_value.cursor.return_value = cursor

        response = self.client.post(
            "/api/auth/forgot-password",
            json={"email": "student@example.com"}
        )

        self.assertEqual(response.status_code, 200)
        mock_db.return_value.commit.assert_called_once()
        mock_email.assert_called_once()

    # Test 3: Nonexistent account
    @patch("app.send_password_reset_email")
    @patch("app.get_db_connection")
    def test_forgot_password_unknown_email(self, mock_db, mock_email):
        cursor = MagicMock()
        cursor.fetchone.return_value = None

        mock_db.return_value.cursor.return_value = cursor

        response = self.client.post(
            "/api/auth/forgot-password",
            json={"email": "missing@example.com"}
        )

        self.assertEqual(response.status_code, 200)
        mock_email.assert_not_called()

        self.assertIn(
            "If an account exists",
            response.json["message"]
        )

    # Test 4: Valid reset token
    @patch("app.get_db_connection")
    def test_reset_password_valid_token(self, mock_db):
        cursor = MagicMock()

        cursor.fetchone.return_value = {
            "user_id": 17,
            "expires_at": datetime.now(timezone.utc).replace(
                tzinfo=None
            ) + timedelta(minutes=10)
        }

        mock_db.return_value.cursor.return_value = cursor

        response = self.client.post(
            "/api/auth/reset-password",
            json={
                "token": "valid-reset-token",
                "password": "NewPassword123!"
            }
        )

        self.assertEqual(response.status_code, 200)
        mock_db.return_value.commit.assert_called_once()

    # Test 5: Invalid reset token
    @patch("app.get_db_connection")
    def test_reset_password_invalid_token(self, mock_db):
        cursor = MagicMock()
        cursor.fetchone.return_value = None

        mock_db.return_value.cursor.return_value = cursor

        response = self.client.post(
            "/api/auth/reset-password",
            json={
                "token": "invalid-token",
                "password": "NewPassword123!"
            }
        )

        self.assertEqual(response.status_code, 400)

    # Test 6: Expired reset token
    @patch("app.get_db_connection")
    def test_reset_password_expired_token(self, mock_db):
        cursor = MagicMock()

        cursor.fetchone.return_value = {
            "user_id": 17,
            "expires_at": datetime.now(timezone.utc).replace(
                tzinfo=None
            ) - timedelta(minutes=1)
        }

        mock_db.return_value.cursor.return_value = cursor

        response = self.client.post(
            "/api/auth/reset-password",
            json={
                "token": "expired-token",
                "password": "NewPassword123!"
            }
        )

        self.assertEqual(response.status_code, 400)
        mock_db.return_value.commit.assert_not_called()

    # Test 7: Reused reset token
    @patch("app.get_db_connection")
    def test_reset_password_reused_token(self, mock_db):
        cursor = MagicMock()

        cursor.fetchone.side_effect = [
            {
                "user_id": 17,
                "expires_at": datetime.now(timezone.utc).replace(
                    tzinfo=None
                ) + timedelta(minutes=10)
            },
            None
        ]

        mock_db.return_value.cursor.return_value = cursor

        first_response = self.client.post(
            "/api/auth/reset-password",
            json={
                "token": "single-use-token",
                "password": "NewPassword123!"
            }
        )

        second_response = self.client.post(
            "/api/auth/reset-password",
            json={
                "token": "single-use-token",
                "password": "AnotherPassword123!"
            }
        )

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 400)

    # Test 8: Password too short
    def test_reset_password_short_password(self):
        response = self.client.post(
            "/api/auth/reset-password",
            json={
                "token": "valid-token",
                "password": "123"
            }
        )

        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            response.json["error"],
            "Password must be at least 8 characters"
        )

    # Test 9: New password is hashed
    @patch("app.get_db_connection")
    def test_reset_password_hashing(self, mock_db):
        cursor = MagicMock()

        cursor.fetchone.return_value = {
            "user_id": 17,
            "expires_at": datetime.now(timezone.utc).replace(
                tzinfo=None
            ) + timedelta(minutes=10)
        }

        mock_db.return_value.cursor.return_value = cursor

        response = self.client.post(
            "/api/auth/reset-password",
            json={
                "token": "valid-token",
                "password": "NewPassword123!"
            }
        )

        self.assertEqual(response.status_code, 200)

        update_call = next(
            call for call in cursor.execute.call_args_list
            if "UPDATE users" in call.args[0]
        )

        saved_hash = update_call.args[1][0]

        self.assertNotEqual(
            saved_hash,
            "NewPassword123!"
        )

        self.assertTrue(
            check_password_hash(
                saved_hash,
                "NewPassword123!"
            )
        )

    # Test 10: Old password no longer works
    @patch("app.get_db_connection")
    def test_old_password_rejected_after_reset(self, mock_db):
        cursor = MagicMock()

        cursor.fetchone.return_value = {
            "user_id": 17,
            "expires_at": datetime.now(timezone.utc).replace(
                tzinfo=None
            ) + timedelta(minutes=10)
        }

        mock_db.return_value.cursor.return_value = cursor

        response = self.client.post(
            "/api/auth/reset-password",
            json={
                "token": "valid-token",
                "password": "NewPassword123!"
            }
        )

        self.assertEqual(response.status_code, 200)

        update_call = next(
            call for call in cursor.execute.call_args_list
            if "UPDATE users" in call.args[0]
        )

        saved_hash = update_call.args[1][0]

        self.assertFalse(
            check_password_hash(
                saved_hash,
                "OldPassword123!"
            )
        )

        self.assertTrue(
            check_password_hash(
                saved_hash,
                "NewPassword123!"
            )
        )


if __name__ == "__main__":
    unittest.main()
