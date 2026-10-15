
import unittest
from unittest.mock import MagicMock, patch

from werkzeug.security import generate_password_hash
from app import app


class AuthenticationApiTests(unittest.TestCase):

    def setUp(self):
        app.config.update(
            TESTING=True,
            SECRET_KEY="testing-only-key"
        )

        self.client = app.test_client()

        self.user = {
            "user_id": 17,
            "username": "student",
            "email": "student@example.com",
            "password_hash": generate_password_hash(
                "correct-password",
                method="pbkdf2:sha256"
            ),
        }

    def tearDown(self):
        app.config["SECRET_KEY"] = "testing-only-key"

        with self.client.session_transaction() as sess:
            sess.clear()

    def login(
        self,
        identity="student@example.com",
        password="correct-password"
    ):
        with patch("app.get_db_connection") as connect:
            cursor = MagicMock()
            cursor.fetchone.return_value = self.user

            connect.return_value.cursor.return_value = cursor

            response = self.client.post(
                "/api/auth/login",
                json={
                    "email": identity,
                    "password": password
                }
            )

            return response, cursor

    # Test 1: Successful login
    def test_successful_login_and_database_query(self):
        response, cursor = self.login()

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.json["user"]["user_id"],
            17
        )

        self.assertNotIn(
            "password_hash",
            response.json["user"]
        )

        self.assertIn(
            "SELECT",
            cursor.execute.call_args.args[0]
        )

        self.assertEqual(
            self.client.get("/api/auth/session").status_code,
            200
        )

    # Test 2: Login using username
    def test_login_by_username(self):
        with patch("app.get_db_connection") as connect:
            connect.return_value.cursor.return_value.fetchone.return_value = self.user

            response = self.client.post(
                "/api/auth/login",
                json={
                    "username": "student",
                    "password": "correct-password"
                }
            )

        self.assertEqual(response.status_code, 200)

    # Test 3: Incorrect password
    def test_invalid_password(self):
        response, _ = self.login(password="wrong")

        self.assertEqual(response.status_code, 401)

        self.assertEqual(
            self.client.get("/api/auth/session").status_code,
            401
        )

    # Test 4: Nonexistent account
    def test_unknown_account(self):
        with patch("app.get_db_connection") as connect:
            connect.return_value.cursor.return_value.fetchone.return_value = None

            response = self.client.post(
                "/api/auth/login",
                json={
                    "email": "missing@example.com",
                    "password": "password"
                }
            )

        self.assertEqual(response.status_code, 401)

    # Test 5: Missing credentials
    def test_missing_credentials(self):
        for payload in (
            {"email": "student@example.com"},
            {"password": "abc"},
            {}
        ):
            with self.subTest(payload=payload):
                response = self.client.post(
                    "/api/auth/login",
                    json=payload
                )

                self.assertEqual(response.status_code, 400)

    # Test 6: Malformed JSON
    def test_malformed_json(self):
        response = self.client.post(
            "/api/auth/login",
            data="bad",
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)

    # Test 7: Logout clears session
    def test_logout_clears_session(self):
        self.login()

        self.assertEqual(
            self.client.post("/api/auth/logout").status_code,
            200
        )

        self.assertEqual(
            self.client.get("/api/auth/session").status_code,
            401
        )

        with self.client.session_transaction() as sess:
            self.assertNotIn("user_id", sess)

    # Test 8: Unauthorized session access
    def test_unauthorized_session_access(self):
        self.assertEqual(
            self.client.get("/api/auth/session").status_code,
            401
        )

    # Test 9: Database error
    def test_database_error(self):
        with patch(
            "app.get_db_connection",
            side_effect=Exception("offline")
        ):
            response = self.client.post(
                "/api/auth/login",
                json={
                    "email": "student@example.com",
                    "password": "password"
                }
            )

        self.assertEqual(response.status_code, 503)

        self.assertNotIn(
            "offline",
            response.get_data(as_text=True)
        )

    # Test 10: Missing secret key
    def test_login_without_secret_key(self):
        app.config["SECRET_KEY"] = None

        response = self.client.post(
            "/api/auth/login",
            json={
                "email": "student@example.com",
                "password": "password"
            }
        )

        self.assertEqual(response.status_code, 503)

    # Test 11: Session persists
    def test_session_persists_across_requests(self):
        self.login()

        self.assertEqual(
            self.client.get("/api/auth/session").status_code,
            200
        )

        self.assertEqual(
            self.client.get("/api/auth/session").json["user_id"],
            17
        )

    # Test 12: Invalid login clears previous session
    def test_invalid_login_clears_previous_session(self):
        self.login()

        self.assertEqual(
            self.client.get("/api/auth/session").status_code,
            200
        )

        response, _ = self.login(password="wrong")

        self.assertEqual(response.status_code, 401)

        self.assertEqual(
            self.client.get("/api/auth/session").status_code,
            401
        )

    # Test 13: Logout without login
    def test_logout_without_login(self):
        self.assertEqual(
            self.client.post("/api/auth/logout").status_code,
            200
        )

        self.assertEqual(
            self.client.get("/api/auth/session").status_code,
            401
        )


if __name__ == "__main__":
    unittest.main()
