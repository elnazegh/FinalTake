"""Sprint 3 backend unit tests. No live database is required."""

import unittest
from unittest.mock import MagicMock, patch

import mysql.connector
from werkzeug.security import check_password_hash

import app as app_module
import database
from app import app


class DatabaseConnectionTests(unittest.TestCase):

    @patch("database.mysql.connector.connect")
    def test_connection_uses_environment_settings(self, mock_connect):
        environment = {
            "DB_HOST": "db.example.test",
            "DB_USER": "unit_user",
            "DB_PASSWORD": "unit_pass",
            "DB_NAME": "unit_db",
        }

        with patch.dict("os.environ", environment, clear=True):
            connection = database.get_db_connection()

        mock_connect.assert_called_once_with(
            host="db.example.test",
            user="unit_user",
            password="unit_pass",
            database="unit_db",
        )
        self.assertIs(connection, mock_connect.return_value)

    @patch("database.mysql.connector.connect")
    def test_connection_does_not_fall_back_to_hardcoded_credentials(
        self, mock_connect
    ):
        with patch.dict("os.environ", {}, clear=True):
            database.get_db_connection()

        _, kwargs = mock_connect.call_args
        self.assertEqual(
            kwargs,
            {"host": None, "user": None, "password": None, "database": None},
        )

    @patch("database.mysql.connector.connect")
    def test_connection_error_is_propagated(self, mock_connect):
        mock_connect.side_effect = mysql.connector.Error("refused")

        with self.assertRaises(mysql.connector.Error):
            database.get_db_connection()


class BaseAppTestCase(unittest.TestCase):

    def setUp(self):
        original_secret_key = app.config.get("SECRET_KEY")
        app.config["SECRET_KEY"] = "backend-unit-tests-only-key"
        self.addCleanup(app.config.__setitem__, "SECRET_KEY", original_secret_key)
        app.config["TESTING"] = True
        self.client = app.test_client()
        with self.client.session_transaction() as session:
            session["user_id"] = 1
        app_module.reviews.clear()
        app_module.next_review_id = 1


class BasicRouteTests(BaseAppTestCase):

    def test_home_route(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(),
            {"message": "FinalTake backend is running"},
        )

    def test_forgot_password_route_is_not_implemented(self):
        response = self.client.post("/api/auth/forgot-password")

        self.assertEqual(response.status_code, 501)


class HealthCheckTests(BaseAppTestCase):

    @patch("app.get_db_connection")
    def test_healthy_when_database_connected(self, mock_get_connection):
        connection = MagicMock()
        connection.is_connected.return_value = True
        mock_get_connection.return_value = connection

        response = self.client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(),
            {"status": "healthy", "database": "connected"},
        )
        connection.close.assert_called_once()

    @patch("app.get_db_connection")
    def test_unhealthy_when_database_disconnected(self, mock_get_connection):
        connection = MagicMock()
        connection.is_connected.return_value = False
        mock_get_connection.return_value = connection

        response = self.client.get("/api/health")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.get_json(),
            {"status": "unhealthy", "database": "disconnected"},
        )

    @patch("app.get_db_connection")
    def test_unhealthy_when_connection_raises(self, mock_get_connection):
        mock_get_connection.side_effect = Exception("connection refused")

        response = self.client.get("/api/health")

        self.assertEqual(response.status_code, 500)

        data = response.get_json()
        self.assertEqual(data["status"], "unhealthy")
        self.assertEqual(data["database"], "disconnected")
        self.assertEqual(data["error"], "connection refused")


class MediaLookupTests(BaseAppTestCase):

    def test_get_media_by_id_accepts_string_and_integer_ids(self):
        self.assertEqual(
            app_module.get_media_by_id("1")["title"], "The Dark Knight"
        )
        self.assertEqual(
            app_module.get_media_by_id(1)["title"], "The Dark Knight"
        )

    def test_get_media_by_id_returns_none_for_invalid_ids(self):
        for media_id in ("999", 0, -1, "", None, "abc"):
            with self.subTest(media_id=media_id):
                self.assertIsNone(app_module.get_media_by_id(media_id))

    def test_catalog_entries_have_required_fields_and_unique_ids(self):
        required = {"id", "title", "type", "genre", "imageUrl", "releaseYear"}
        ids = [media["id"] for media in app_module.media_items]

        self.assertEqual(len(ids), len(set(ids)))

        for media in app_module.media_items:
            with self.subTest(media_id=media["id"]):
                self.assertTrue(required.issubset(media))
                self.assertTrue(media["title"].strip())

    def test_every_catalog_item_is_retrievable_by_id(self):
        for media in app_module.media_items:
            with self.subTest(media_id=media["id"]):
                response = self.client.get(f"/api/media/{media['id']}")

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.get_json(), media)

    def test_nonexistent_media_id_returns_404(self):
        response = self.client.get("/api/media/999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.get_json(), {"error": "Media not found."}
        )

    def test_media_id_boundaries_return_404(self):
        for media_id in ("0", "-1", "abc", "1.5"):
            with self.subTest(media_id=media_id):
                response = self.client.get(f"/api/media/{media_id}")

                self.assertEqual(response.status_code, 404)


class SearchEdgeCaseTests(BaseAppTestCase):

    def search(self, **params):
        return self.client.get("/api/search", query_string=params)

    def test_exact_title_returns_only_that_title(self):
        titles = [m["title"] for m in self.search(query="Dune").get_json()["results"]]

        self.assertEqual(titles, ["Dune"])

    def test_whitespace_only_query_returns_no_results(self):
        response = self.search(query="    ")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"results": []})

    def test_filters_without_query_return_no_results(self):
        response = self.search(genre="Drama", media_type="movie")

        self.assertEqual(response.get_json(), {"results": []})

    def test_wildcard_characters_are_matched_literally(self):
        for query in ("%", "_", "d%k", "*"):
            with self.subTest(query=query):
                self.assertEqual(
                    self.search(query=query).get_json(), {"results": []}
                )

    def test_very_long_query_returns_no_results(self):
        response = self.search(query="a" * 5000)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"results": []})

    def test_filters_are_case_insensitive(self):
        results = self.search(
            query="dark", genre="DRAMA", media_type="MOVIE"
        ).get_json()["results"]

        self.assertEqual([m["title"] for m in results], ["Darkest Hour"])

    def test_sort_title_descending(self):
        results = self.search(query="dark", sort="title_desc").get_json()["results"]
        titles = [m["title"] for m in results]

        self.assertEqual(titles, sorted(titles, key=str.casefold, reverse=True))

    def test_sort_year_ascending(self):
        results = self.search(query="dark", sort="year_asc").get_json()["results"]
        years = [m["releaseYear"] for m in results]

        self.assertEqual(years, sorted(years))

    def test_unknown_sort_keeps_catalog_order(self):
        results = self.search(query="dark", sort="not_a_sort").get_json()["results"]
        ids = [m["id"] for m in results]

        self.assertEqual(ids, ["1", "2", "3", "5"])


class ReviewValidationTests(BaseAppTestCase):

    def post_review(self, **overrides):
        payload = {
            "media_id": "1",
            "rating": 4.5,
            "text": "Great movie.",
        }
        payload.update(overrides)

        return self.client.post("/api/reviews", json=payload)

    def test_each_required_field_is_enforced(self):
        for field in ("media_id", "rating", "text"):
            with self.subTest(field=field):
                payload = {
                    "media_id": "1",
                    "rating": 4.5,
                    "text": "Great movie.",
                }
                del payload[field]

                response = self.client.post("/api/reviews", json=payload)

                self.assertEqual(response.status_code, 400)

        self.assertEqual(app_module.reviews, {})

    def test_review_creation_requires_authenticated_session(self):
        with self.client.session_transaction() as session:
            session.clear()

        response = self.post_review()

        self.assertEqual(response.status_code, 401)
        self.assertEqual(app_module.reviews, {})

    def test_empty_json_body_is_rejected(self):
        response = self.client.post("/api/reviews", json={})

        self.assertEqual(response.status_code, 400)

    def test_malformed_body_is_rejected(self):
        response = self.client.post(
            "/api/reviews",
            data="not json",
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)

    def test_valid_rating_boundaries_are_accepted(self):
        for rating in (0.5, 1, 2.5, 5, 5.0):
            with self.subTest(rating=rating):
                response = self.post_review(rating=rating)

                self.assertEqual(response.status_code, 201)
                self.assertEqual(
                    response.get_json()["review"]["rating"], float(rating)
                )

    def test_invalid_rating_boundaries_are_rejected(self):
        for rating in (0, 0.4, 0.75, 5.5, 6, -1, "5", [5]):
            with self.subTest(rating=rating):
                response = self.post_review(rating=rating)

                self.assertEqual(response.status_code, 400)

        self.assertEqual(app_module.reviews, {})

    def test_review_text_length_boundary(self):
        at_limit = self.post_review(text="a" * 5000)
        over_limit = self.post_review(text="a" * 5001)

        self.assertEqual(at_limit.status_code, 201)
        self.assertEqual(over_limit.status_code, 400)
        self.assertEqual(len(app_module.reviews), 1)

    def test_blank_and_non_string_text_are_rejected(self):
        for text in ("", "   ", "\n\t", 123, ["text"]):
            with self.subTest(text=text):
                response = self.post_review(text=text)

                self.assertEqual(response.status_code, 400)

        self.assertEqual(app_module.reviews, {})

    def test_review_text_is_trimmed(self):
        response = self.post_review(text="  padded  ")

        self.assertEqual(response.get_json()["review"]["text"], "padded")

    def test_media_id_may_be_sent_as_integer(self):
        response = self.post_review(media_id=2)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["review"]["media_id"], "2")
        self.assertEqual(response.get_json()["review"]["media_title"], "Dark")

    def test_review_ids_are_not_reused_after_delete(self):
        first_id = self.post_review().get_json()["review"]["id"]
        self.client.delete(f"/api/reviews/{first_id}", json={"user_id": 1})

        second_id = self.post_review().get_json()["review"]["id"]

        self.assertNotEqual(first_id, second_id)

    def test_missing_review_returns_404_for_every_method(self):
        responses = [
            self.client.get("/api/reviews/999"),
            self.client.patch("/api/reviews/999", json={"text": "x"}),
            self.client.delete("/api/reviews/999", json={}),
        ]

        for response in responses:
            with self.subTest(status=response.status_code):
                self.assertEqual(response.status_code, 404)
                self.assertEqual(
                    response.get_json(), {"error": "Review not found."}
                )

    def test_get_reviews_for_media_without_reviews_is_empty(self):
        self.post_review(media_id="1")

        response = self.client.get("/api/reviews", query_string={"media_id": "4"})

        self.assertEqual(response.get_json(), {"reviews": []})

    def test_edit_requires_text_but_uses_session_identity(self):
        review_id = self.post_review().get_json()["review"]["id"]

        for payload in ({}, {"user_id": 1}):
            with self.subTest(payload=payload):
                response = self.client.patch(
                    f"/api/reviews/{review_id}", json=payload
                )

                self.assertEqual(response.status_code, 400)

        response = self.client.patch(
            f"/api/reviews/{review_id}", json={"text": "Updated."}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["review"]["user_id"], 1)

    def test_failed_edits_leave_review_unchanged(self):
        review_id = self.post_review(text="Original.").get_json()["review"]["id"]

        empty_text = self.client.patch(
            f"/api/reviews/{review_id}", json={"text": "  "}
        )
        too_long = self.client.patch(
            f"/api/reviews/{review_id}", json={"text": "a" * 5001}
        )
        with self.client.session_transaction() as session:
            session["user_id"] = 2
        wrong_owner = self.client.patch(
            f"/api/reviews/{review_id}", json={"text": "Hijack."}
        )

        self.assertEqual(empty_text.status_code, 400)
        self.assertEqual(too_long.status_code, 400)
        self.assertEqual(wrong_owner.status_code, 403)
        self.assertEqual(app_module.reviews[review_id].text, "Original.")

    def test_delete_uses_session_identity_without_body_user_id(self):
        review_id = self.post_review().get_json()["review"]["id"]

        response = self.client.delete(f"/api/reviews/{review_id}", json={})

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(review_id, app_module.reviews)

    def test_non_owner_delete_keeps_review(self):
        review_id = self.post_review().get_json()["review"]["id"]

        with self.client.session_transaction() as session:
            session["user_id"] = 2

        response = self.client.delete(f"/api/reviews/{review_id}", json={})

        self.assertEqual(response.status_code, 403)
        self.assertIn(review_id, app_module.reviews)

    def test_deleted_review_is_no_longer_retrievable(self):
        review_id = self.post_review().get_json()["review"]["id"]

        deleted = self.client.delete(
            f"/api/reviews/{review_id}", json={}
        )
        fetched = self.client.get(f"/api/reviews/{review_id}")

        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(fetched.status_code, 404)


class RegistrationDatabaseHandlingTests(BaseAppTestCase):
    """Registration behaviour with the database mocked out."""

    valid_payload = {
        "username": "unit_user",
        "email": "unit@example.com",
        "password": "password123",
    }

    def setUp(self):
        super().setUp()

        patcher = patch("app.get_db_connection")
        self.mock_get_connection = patcher.start()
        self.addCleanup(patcher.stop)

        self.connection = MagicMock()
        self.cursor = MagicMock()
        self.connection.cursor.return_value = self.cursor
        self.mock_get_connection.return_value = self.connection

    def register(self, **overrides):
        payload = {**self.valid_payload, **overrides}

        return self.client.post("/api/auth/register", json=payload)

    def test_success_commits_and_releases_resources(self):
        response = self.register()

        self.assertEqual(response.status_code, 201)
        self.connection.commit.assert_called_once()
        self.connection.rollback.assert_not_called()
        self.cursor.close.assert_called_once()
        self.connection.close.assert_called_once()

    def test_insert_uses_bound_parameters(self):
        self.register(username="o'brien; DROP TABLE users;--")

        sql, parameters = self.cursor.execute.call_args.args

        self.assertIn("%s", sql)
        self.assertNotIn("DROP TABLE", sql)
        self.assertEqual(parameters[0], "o'brien; DROP TABLE users;--")
        self.assertEqual(parameters[1], "unit@example.com")

    def test_stored_password_is_salted_pbkdf2_hash(self):
        self.register()
        first_hash = self.cursor.execute.call_args.args[1][2]

        self.register()
        second_hash = self.cursor.execute.call_args.args[1][2]

        self.assertTrue(first_hash.startswith("pbkdf2:sha256"))
        self.assertTrue(check_password_hash(first_hash, "password123"))
        self.assertNotEqual(first_hash, second_hash)

    def test_empty_fields_are_rejected_before_database_access(self):
        for field in ("username", "email", "password"):
            with self.subTest(field=field):
                response = self.register(**{field: ""})

                self.assertEqual(response.status_code, 400)

        self.mock_get_connection.assert_not_called()

    def test_empty_json_body_is_rejected(self):
        response = self.client.post("/api/auth/register", json={})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_json(), {"error": "Request body is required"}
        )
        self.mock_get_connection.assert_not_called()

    def test_non_json_body_is_rejected(self):
        response = self.client.post(
            "/api/auth/register", data="username=a", content_type="text/plain"
        )

        self.assertIn(response.status_code, (400, 415))
        self.mock_get_connection.assert_not_called()

    def test_invalid_email_formats_are_rejected(self):
        for email in ("plain", "a@b", "@b.com", "a b@c.com", "a@@b.com", "a@b c.com"):
            with self.subTest(email=email):
                response = self.register(email=email)

                self.assertEqual(response.status_code, 400)

        self.mock_get_connection.assert_not_called()

    def test_minimal_valid_email_is_accepted(self):
        response = self.register(email="a@b.co")

        self.assertEqual(response.status_code, 201)

    def test_duplicate_entry_returns_409_and_rolls_back(self):
        self.cursor.execute.side_effect = Exception("Duplicate entry 'x'")

        response = self.register()

        self.assertEqual(response.status_code, 409)
        self.connection.rollback.assert_called_once()
        self.connection.commit.assert_not_called()
        self.connection.close.assert_called_once()

    def test_unexpected_database_error_returns_500_without_details(self):
        self.cursor.execute.side_effect = Exception("secret internal detail")

        response = self.register()

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.get_json(), {"error": "Registration failed"})
        self.connection.rollback.assert_called_once()
        self.connection.commit.assert_not_called()
        self.cursor.close.assert_called_once()
        self.connection.close.assert_called_once()

    def test_commit_failure_is_rolled_back(self):
        self.connection.commit.side_effect = Exception("commit failed")

        response = self.register()

        self.assertEqual(response.status_code, 500)
        self.connection.rollback.assert_called_once()

    def test_unreachable_database_returns_500(self):
        self.mock_get_connection.side_effect = mysql.connector.Error("down")

        with patch.dict(
            app.config, {"TESTING": False, "PROPAGATE_EXCEPTIONS": False}
        ), self.assertLogs(app.logger, level="ERROR"):
            response = app.test_client().post(
                "/api/auth/register", json=self.valid_payload
            )

        self.assertEqual(response.status_code, 500)


if __name__ == "__main__":
    unittest.main()
