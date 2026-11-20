
"""Review persistence tests using SQLite as a lightweight SQL test double.

Production uses MySQL. These tests validate SQL-backed behavior and Flask API
integration without needing a shared MySQL server or modifying user data.
"""

import os
import sqlite3
import tempfile
import unittest

from backend.review import Review
from backend.review_storage import MySQLReviewStore


class SQLiteCursorAdapter:
    def __init__(self, connection, dictionary=False):
        self.cursor = connection.cursor()
        self.dictionary = dictionary

    def execute(self, sql, values=()):
        self.cursor.execute(sql.replace("%s", "?"), values)

    def _format(self, row):
        if row is None or not self.dictionary:
            return row
        names = [column[0] for column in self.cursor.description]
        return dict(zip(names, row))

    def fetchone(self):
        return self._format(self.cursor.fetchone())

    def fetchall(self):
        return [self._format(row) for row in self.cursor.fetchall()]

    @property
    def rowcount(self):
        return self.cursor.rowcount

    @property
    def lastrowid(self):
        return self.cursor.lastrowid

    def close(self):
        self.cursor.close()


class SQLiteConnectionAdapter:
    def __init__(self, database_file):
        self.connection = sqlite3.connect(database_file)

    def cursor(self, dictionary=False):
        return SQLiteCursorAdapter(self.connection, dictionary)

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()

    def close(self):
        self.connection.close()


class ReviewSQLFixture:
    """Shared fixture for repository and Flask route tests."""

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.database_file = os.path.join(
            self.tempdir.name, "test_reviews.sqlite3"
        )

        # A sqlite3 connection context manager commits or rolls back,
        # but does not close the connection. Close it explicitly so
        # Windows can remove the temporary database after testing.
        connection = sqlite3.connect(self.database_file)
        try:
            connection.execute(
                """
                CREATE TABLE reviews (
                    review_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    media_id TEXT NOT NULL,
                    rating NUMERIC NOT NULL,
                    review_text TEXT NOT NULL,
                    tags_json TEXT NOT NULL
                )
                """
            )
            connection.commit()
        finally:
            connection.close()

        self.factory = lambda: SQLiteConnectionAdapter(
            self.database_file
        )
        self.store = MySQLReviewStore(self.factory)

    def create_example(self, text="Original review", tags=None):
        return self.store.create(
            Review(1, "1", 4.5, text, tags)
        )


class ReviewSQLStoreTests(ReviewSQLFixture, unittest.TestCase):
    def test_create_and_read_after_new_store_instance(self):
        review_id = self.create_example(tags="Drama, sci fi")
        restarted_store = MySQLReviewStore(self.factory)
        review = restarted_store.get(review_id)

        self.assertEqual(review.user_id, 1)
        self.assertEqual(review.media_id, "1")
        self.assertEqual(review.rating, 4.5)
        self.assertEqual(review.text, "Original review")
        self.assertEqual(review.tags, ["drama", "sci fi"])

    def test_list_filters_by_media_and_complete_tag(self):
        self.create_example(tags="Drama")
        self.store.create(
            Review(2, "2", 3.5, "Another review", ["drama"])
        )
        self.store.create(
            Review(1, "1", 5.0, "Different tag", ["comedy"])
        )

        found = self.store.list(media_id="1", tag="drama")

        self.assertEqual(len(found), 1)
        self.assertEqual(found[0][1].text, "Original review")

    def test_update_survives_new_connection(self):
        review_id = self.create_example()
        self.store.update_text(review_id, 1, "Updated review")

        self.assertEqual(
            MySQLReviewStore(self.factory).get(review_id).text,
            "Updated review",
        )

    def test_deletion_survives_new_connection(self):
        review_id = self.create_example()
        self.store.delete(review_id, 1)

        self.assertIsNone(
            MySQLReviewStore(self.factory).get(review_id)
        )

    def test_owner_id_is_required_for_sql_update_and_delete(self):
        review_id = self.create_example()

        with self.assertRaises(RuntimeError):
            self.store.update_text(review_id, 99, "Unauthorized")

        with self.assertRaises(RuntimeError):
            self.store.delete(review_id, 99)

        self.assertEqual(
            self.store.get(review_id).text,
            "Original review",
        )


try:
    from backend import app as app_module
except ImportError:
    app_module = None


@unittest.skipIf(
    app_module is None,
    "Flask unavailable in this environment",
)
class ReviewSQLApiTests(ReviewSQLFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()

        self.old_backend = app_module.app.config.get(
            "REVIEW_STORAGE_BACKEND"
        )
        self.old_key = app_module.app.config.get("SECRET_KEY")
        self.old_store = app_module.mysql_review_store

        app_module.app.config.update(
            TESTING=True,
            SECRET_KEY="review-sql-test-key",
            REVIEW_STORAGE_BACKEND="mysql",
        )

        app_module.mysql_review_store = self.store
        self.client = app_module.app.test_client()
        self.authenticate(1)

    def tearDown(self):
        app_module.app.config.update(
            REVIEW_STORAGE_BACKEND=self.old_backend,
            SECRET_KEY=self.old_key,
        )
        app_module.mysql_review_store = self.old_store

    def authenticate(self, user_id):
        with self.client.session_transaction() as user_session:
            user_session["user_id"] = user_id

    def test_api_create_persists_and_get_works(self):
        response = self.client.post(
            "/api/reviews",
            json={
                "media_id": "1",
                "rating": 4.5,
                "text": "Persist me",
                "tags": "drama",
            },
        )

        self.assertEqual(response.status_code, 201)

        review_id = response.get_json()["review"]["id"]
        app_module.mysql_review_store = MySQLReviewStore(
            self.factory
        )

        found = self.client.get(f"/api/reviews/{review_id}")

        self.assertEqual(found.status_code, 200)
        self.assertEqual(
            found.get_json()["review"]["text"],
            "Persist me",
        )
        self.assertEqual(
            found.get_json()["review"]["tags"],
            ["drama"],
        )

    def test_api_owner_edit_and_delete_persist(self):
        review_id = self.create_example()

        response = self.client.patch(
            f"/api/reviews/{review_id}",
            json={"text": "Edited"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.store.get(review_id).text,
            "Edited",
        )

        response = self.client.delete(
            f"/api/reviews/{review_id}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(self.store.get(review_id))

    def test_api_non_owner_cannot_edit_delete_even_with_forged_id(self):
        review_id = self.create_example()
        self.authenticate(2)

        response = self.client.patch(
            f"/api/reviews/{review_id}",
            json={
                "user_id": 1,
                "text": "Forged",
            },
        )

        self.assertEqual(response.status_code, 403)

        response = self.client.delete(
            f"/api/reviews/{review_id}",
            json={"user_id": 1},
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            self.store.get(review_id).text,
            "Original review",
        )

    def test_api_tag_filter(self):
        self.create_example(tags="drama")

        self.store.create(
            Review(2, "1", 4.0, "Other", tags="comedy")
        )

        response = self.client.get(
            "/api/reviews?media_id=1&tag=drama"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            len(response.get_json()["reviews"]),
            1,
        )

    def test_api_rejects_invalid_review_without_writing(self):
        response = self.client.post(
            "/api/reviews",
            json={
                "media_id": "1",
                "rating": 7.0,
                "text": "Invalid",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.store.list(), [])


if __name__ == "__main__":
    unittest.main()
