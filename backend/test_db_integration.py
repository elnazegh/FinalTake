"""Sprint 3 backend/database integration tests.

Exercises the Flask routes against a real MySQL test database. Skipped when
no test MySQL server is configured (see db_test_support.py).
"""

import unittest
from unittest.mock import patch

from werkzeug.security import check_password_hash

import app as app_module
from app import app
from db_test_support import MySQLTestCase


class RegistrationDatabaseIntegrationTests(MySQLTestCase):

    def setUp(self):
        super().setUp()

        app.config["TESTING"] = True
        self.client = app.test_client()

        patcher = patch("app.get_db_connection", side_effect=self.connect)
        patcher.start()
        self.addCleanup(patcher.stop)

    def register(self, username="alice", email="alice@example.com", password="password123"):
        return self.client.post(
            "/api/auth/register",
            json={"username": username, "email": email, "password": password},
        )

    def test_registration_persists_user_with_hashed_password(self):
        response = self.register()

        self.assertEqual(response.status_code, 201)

        rows = self.fetch_all("SELECT username, email, password_hash FROM users")

        self.assertEqual(len(rows), 1)

        username, email, password_hash = rows[0]

        self.assertEqual((username, email), ("alice", "alice@example.com"))
        self.assertNotEqual(password_hash, "password123")
        self.assertTrue(check_password_hash(password_hash, "password123"))

    def test_multiple_users_are_stored_independently(self):
        self.assertEqual(self.register("one", "one@example.com").status_code, 201)
        self.assertEqual(self.register("two", "two@example.com").status_code, 201)

        usernames = sorted(row[0] for row in self.fetch_all("SELECT username FROM users"))

        self.assertEqual(usernames, ["one", "two"])

    def test_duplicate_username_returns_409_and_keeps_original_user(self):
        self.register("dupe", "first@example.com")

        response = self.register("dupe", "second@example.com")

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            self.fetch_all("SELECT username, email FROM users"),
            [("dupe", "first@example.com")],
        )

    def test_duplicate_email_returns_409_and_keeps_original_user(self):
        self.register("first", "dupe@example.com")

        response = self.register("second", "dupe@example.com")

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            self.fetch_all("SELECT username, email FROM users"),
            [("first", "dupe@example.com")],
        )

    def test_invalid_requests_do_not_create_rows(self):
        invalid_payloads = [
            {"email": "a@example.com", "password": "pw"},
            {"username": "a", "password": "pw"},
            {"username": "a", "email": "a@example.com"},
            {"username": "a", "email": "not-an-email", "password": "pw"},
            {"username": "", "email": "a@example.com", "password": "pw"},
        ]

        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                response = self.client.post("/api/auth/register", json=payload)

                self.assertEqual(response.status_code, 400)

        self.assertEqual(self.count_users(), 0)

    def test_over_length_username_fails_cleanly_without_a_row(self):
        response = self.register("u" * 51, "long@example.com")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.get_json(), {"error": "Registration failed"})
        self.assertEqual(self.count_users(), 0)

    def test_sql_metacharacters_in_username_are_stored_literally(self):
        hostile = "x'; DROP TABLE users; --"

        response = self.register(hostile, "hostile@example.com")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            self.fetch_all("SELECT username FROM users"), [(hostile,)]
        )

    def test_registration_is_repeatable_after_cleanup(self):
        self.assertEqual(self.register().status_code, 201)

        self.clear_tables()

        self.assertEqual(self.register().status_code, 201)
        self.assertEqual(self.count_users(), 1)


class HealthCheckDatabaseIntegrationTests(MySQLTestCase):

    def test_health_check_reports_connected_database(self):
        app.config["TESTING"] = True

        with patch("app.get_db_connection", side_effect=self.connect):
            response = app.test_client().get("/api/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(),
            {"status": "healthy", "database": "connected"},
        )

    def test_health_check_reports_unreachable_database(self):
        app.config["TESTING"] = True

        with patch("app.get_db_connection", side_effect=OSError("down")):
            response = app.test_client().get("/api/health")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.get_json()["status"], "unhealthy")


class MediaCatalogInterfaceTests(unittest.TestCase):
    """Media and reviews are in-memory today, so these need no database.

    They exercise the real catalog interface end to end (search -> retrieve by
    ID) so the same checks can be pointed at MySQL once media is persisted.
    """

    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()
        app_module.reviews.clear()

    def test_search_result_can_be_retrieved_by_its_id(self):
        results = self.client.get(
            "/api/search", query_string={"query": "Dune"}
        ).get_json()["results"]

        self.assertEqual(len(results), 1)

        detail = self.client.get(f"/api/media/{results[0]['id']}")

        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.get_json(), results[0])

    def test_partial_search_matches_are_all_retrievable(self):
        results = self.client.get(
            "/api/search", query_string={"query": "dark"}
        ).get_json()["results"]

        self.assertGreater(len(results), 1)

        for media in results:
            with self.subTest(media_id=media["id"]):
                detail = self.client.get(f"/api/media/{media['id']}")

                self.assertEqual(detail.get_json()["title"], media["title"])

    def test_search_with_no_match_and_unknown_id_are_consistent(self):
        search = self.client.get("/api/search", query_string={"query": "zzzz"})
        detail = self.client.get("/api/media/424242")

        self.assertEqual(search.get_json(), {"results": []})
        self.assertEqual(detail.status_code, 404)

    def test_review_for_retrieved_media_round_trips(self):
        created = self.client.post(
            "/api/reviews",
            json={"user_id": 1, "media_id": "4", "rating": 4.0, "text": "Epic."},
        )
        review_id = created.get_json()["review"]["id"]

        fetched = self.client.get(f"/api/reviews/{review_id}").get_json()["review"]

        self.assertEqual(fetched["media_title"], "Dune")
        self.assertEqual(fetched["text"], "Epic.")


if __name__ == "__main__":
    unittest.main()
