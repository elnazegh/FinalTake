import unittest
from unittest.mock import MagicMock, patch

from app import app
from media import update_media_record

ROW = {
    "media_id": 42,
    "title": "Sprint 5 Demo Movie",
    "media_type": "movie",
    "genre": "Adventure",
    "image_url": None,
    "release_year": 2026,
    "description": "A sample adventure movie used to demonstrate database updates.",
}


class UpdateMediaTests(unittest.TestCase):
    def setUp(self):
        self.secret_key = app.config["SECRET_KEY"]
        app.config.update(TESTING=True, SECRET_KEY="update-test-key")
        self.client = app.test_client()
        self.connection = MagicMock()
        self.permission_cursor = MagicMock()
        self.update_cursor = MagicMock()
        self.permission_cursor.fetchone.return_value = (1,)
        self.update_cursor.fetchone.side_effect = [{"media_id": 42}, ROW]
        self.connection.cursor.side_effect = [
            self.permission_cursor, self.update_cursor
        ]
        self.db = patch("app.get_db_connection", return_value=self.connection)
        self.db.start()
        self.addCleanup(self.db.stop)

    def tearDown(self):
        app.config["SECRET_KEY"] = self.secret_key

    def login(self):
        with self.client.session_transaction() as session:
            session["user_id"] = 1

    def test_partial_multiple_field_update_and_parameterization(self):
        self.login()
        response = self.client.patch("/api/media/42", json={
            "genre": "Adventure",
            "description": ROW["description"],
            "imageUrl": None,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {
            "id": "42", "title": ROW["title"], "type": "movie",
            "genre": "Adventure", "imageUrl": None, "releaseYear": 2026,
            "description": ROW["description"],
        })
        update = self.update_cursor.execute.call_args_list[1].args
        expected_sql = (
            "UPDATE media SET genre = %s, image_url = %s, description = %s "
            "WHERE media_id = %s"
        )
        self.assertEqual(
            update,
            (
                expected_sql,
                ("Adventure", None, ROW["description"], 42)
            )
        )
        self.connection.commit.assert_called_once()
        self.connection.rollback.assert_not_called()
        self.connection.close.assert_called_once()

    def test_unchanged_values_still_return_the_record(self):
        self.login()
        self.update_cursor.rowcount = 0
        response = self.client.patch("/api/media/42", json={"genre": "Adventure"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["id"], "42")
        self.connection.commit.assert_called_once()

    def test_missing_media_returns_404(self):
        self.login()
        self.update_cursor.fetchone.side_effect = [None]
        response = self.client.patch("/api/media/999", json={"title": "New"})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.update_cursor.execute.call_count, 1)
        self.connection.commit.assert_not_called()
        self.connection.rollback.assert_called_once()

    def test_unauthenticated_and_non_manager(self):
        response = self.client.patch("/api/media/42", json={"title": "New"})
        self.assertEqual(response.status_code, 401)
        self.connection.cursor.assert_not_called()
        self.login()
        self.permission_cursor.fetchone.return_value = None
        response = self.client.patch("/api/media/42", json={"title": "New"})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.connection.cursor.call_count, 1)

    def test_invalid_payloads(self):
        self.login()
        cases = [
            {}, [], None, {"unknown": "x"}, {"media_id": 1},
            {"title": None}, {"title": " "}, {"title": "x" * 256},
            {"type": None}, {"type": "podcast"},
            {"releaseYear": 999}, {"releaseYear": 9999},
            {"releaseYear": True}, {"releaseYear": "2026"},
            {"genre": 2}, {"genre": "x" * 101},
            {"description": "x" * 5001}, {"imageUrl": "javascript:alert(1)"},
        ]
        for data in cases:
            with self.subTest(data=data):
                self.connection.cursor.side_effect = None
                self.connection.cursor.return_value = self.permission_cursor
                response = self.client.patch("/api/media/42", json=data)
                self.assertEqual(response.status_code, 400)
        self.update_cursor.execute.assert_not_called()
        self.connection.commit.assert_not_called()

    def test_database_failures_are_safe_and_roll_back(self):
        self.login()
        self.update_cursor.execute.side_effect = [None, RuntimeError("secret")]
        response = self.client.patch("/api/media/42", json={"title": "New"})
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.get_json(), {"error": "Unable to update media item."})
        self.connection.rollback.assert_called_once()
        self.connection.commit.assert_not_called()
        self.connection.close.assert_called_once()

    def test_connection_failure_is_safe(self):
        self.login()
        self.db.stop()
        with patch("app.get_db_connection", side_effect=RuntimeError("secret")):
            response = self.client.patch("/api/media/42", json={"title": "New"})
        self.assertEqual(response.status_code, 500)
        self.assertNotIn("secret", response.get_data(as_text=True))

    def test_commit_failure_rolls_back(self):
        self.connection.cursor.side_effect = None
        self.connection.cursor.return_value = self.update_cursor
        self.connection.commit.side_effect = RuntimeError("commit failed")
        with self.assertRaises(RuntimeError):
            update_media_record(self.connection, 42, {"genre": None})
        self.connection.rollback.assert_called_once()

    def test_sql_injection_is_a_parameter(self):
        self.login()
        title = "Name'); DROP TABLE media;--"
        response = self.client.patch("/api/media/42", json={"title": title})
        self.assertEqual(response.status_code, 200)
        sql, params = self.update_cursor.execute.call_args_list[1].args
        self.assertNotIn(title, sql)
        self.assertEqual(params, (title, 42))


if __name__ == "__main__":
    unittest.main()
