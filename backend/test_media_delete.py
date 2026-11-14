import secrets
import unittest
from unittest.mock import MagicMock, patch

from app import app
from media import delete_media_record, get_media, list_media, search_media
from migrate_media_soft_delete import migrate_media_soft_delete
from seed_media import DEMO_MEDIA, seed_demo_media


class DeleteMediaTests(unittest.TestCase):
    def setUp(self):
        self.secret_key = app.config["SECRET_KEY"]
        app.config.update(TESTING=True, SECRET_KEY=secrets.token_hex(32))
        self.client = app.test_client()
        self.connection = MagicMock()
        self.permission_cursor = MagicMock()
        self.delete_cursor = MagicMock()
        self.permission_cursor.fetchone.return_value = (1,)
        self.delete_cursor.rowcount = 1
        self.connection.cursor.side_effect = [
            self.permission_cursor, self.delete_cursor
        ]
        self.db = patch("app.get_db_connection", return_value=self.connection)
        self.db.start()
        self.addCleanup(self.db.stop)

    def tearDown(self):
        app.config["SECRET_KEY"] = self.secret_key

    def login(self):
        with self.client.session_transaction() as session:
            session["user_id"] = 1

    def test_successful_delete_is_parameterized_and_committed(self):
        self.login()
        response = self.client.delete("/api/media/42")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"message": "Media deleted successfully."})
        sql, params = self.delete_cursor.execute.call_args.args
        self.assertIn("deleted_at = CURRENT_TIMESTAMP", sql)
        self.assertIn("deleted_at IS NULL", sql)
        self.assertNotIn("DELETE FROM", sql)
        self.assertEqual(params, (42,))
        self.connection.commit.assert_called_once()
        self.connection.rollback.assert_not_called()
        self.connection.close.assert_called_once()

    def test_missing_or_previously_deleted_returns_404(self):
        self.login()
        self.delete_cursor.rowcount = 0
        response = self.client.delete("/api/media/42")
        self.assertEqual(response.status_code, 404)
        self.connection.commit.assert_called_once()

    def test_authentication_and_authorization(self):
        response = self.client.delete("/api/media/42")
        self.assertEqual(response.status_code, 401)
        self.connection.cursor.assert_not_called()
        self.login()
        self.permission_cursor.fetchone.return_value = None
        response = self.client.delete("/api/media/42")
        self.assertEqual(response.status_code, 403)
        self.delete_cursor.execute.assert_not_called()
        self.connection.commit.assert_not_called()

    def test_connection_failure_is_generic(self):
        self.login()
        self.db.stop()
        with patch("app.get_db_connection", side_effect=RuntimeError("private")):
            response = self.client.delete("/api/media/42")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.get_json(), {"error": "Unable to delete media item."})

    def test_query_and_commit_failures_roll_back(self):
        self.login()
        self.delete_cursor.execute.side_effect = RuntimeError("private SQL details")
        response = self.client.delete("/api/media/42")
        self.assertEqual(response.status_code, 500)
        self.assertNotIn("private", response.get_data(as_text=True))
        self.connection.rollback.assert_called_once()
        self.connection.commit.assert_not_called()

        connection = MagicMock()
        connection.commit.side_effect = RuntimeError("commit failure")
        with self.assertRaises(RuntimeError):
            delete_media_record(connection, 42)
        connection.rollback.assert_called_once()

        connection = MagicMock()
        connection.cursor.side_effect = RuntimeError("cursor failure")
        with self.assertRaises(RuntimeError):
            delete_media_record(connection, 42)
        connection.rollback.assert_called_once()

    def test_invalid_ids_do_not_execute_sql(self):
        for value in (0, -1, True, "1 OR 1=1"):
            self.assertFalse(delete_media_record(self.connection, value))
        self.connection.cursor.assert_not_called()

    def test_public_queries_exclude_deleted_but_review_lookup_can_resolve(self):
        connection = MagicMock()
        cursor = connection.cursor.return_value
        list_media(connection)
        self.assertIn("deleted_at IS NULL", cursor.execute.call_args.args[0])
        search_media(connection, "title")
        self.assertIn("deleted_at IS NULL", cursor.execute.call_args.args[0])
        cursor.fetchone.return_value = None
        get_media(connection, 42)
        self.assertIn("deleted_at IS NULL", cursor.execute.call_args.args[0])
        get_media(connection, 42, include_deleted=True)
        self.assertNotIn("deleted_at IS NULL", cursor.execute.call_args.args[0])


class SoftDeleteMigrationTests(unittest.TestCase):
    def test_adds_column_only_when_missing_and_inspects_constraints_first(self):
        connection = MagicMock()
        cursor = connection.cursor.return_value
        cursor.fetchone.side_effect = [{"TABLE_NAME": "media"}, None]
        cursor.fetchall.return_value = [{"CONSTRAINT_NAME": "fk_media"}]
        added, constraints = migrate_media_soft_delete(connection)
        self.assertTrue(added)
        self.assertEqual(constraints[0]["CONSTRAINT_NAME"], "fk_media")
        queries = [call.args[0] for call in cursor.execute.call_args_list]
        self.assertIn("information_schema.KEY_COLUMN_USAGE", queries[1])
        self.assertIn("ALTER TABLE media ADD COLUMN", queries[-1])

    def test_repeat_and_incompatible_column(self):
        for column, raises in (
            ({"DATA_TYPE": "timestamp", "IS_NULLABLE": "YES",
              "COLUMN_DEFAULT": None, "EXTRA": ""}, False),
            ({"DATA_TYPE": "timestamp", "IS_NULLABLE": "NO",
              "COLUMN_DEFAULT": None, "EXTRA": ""}, True),
        ):
            with self.subTest(column=column):
                connection = MagicMock()
                cursor = connection.cursor.return_value
                cursor.fetchone.side_effect = [{"TABLE_NAME": "media"}, column]
                if raises:
                    with self.assertRaises(RuntimeError):
                        migrate_media_soft_delete(connection)
                else:
                    added, _ = migrate_media_soft_delete(connection)
                    self.assertFalse(added)
                self.assertFalse(any(
                    "ALTER TABLE" in call.args[0]
                    for call in cursor.execute.call_args_list
                ))

    def test_soft_deleted_legacy_row_is_not_recreated(self):
        connection = MagicMock()
        cursor = connection.cursor.return_value
        cursor.fetchone.side_effect = [
            {**record, "deleted_at": "2026-01-01 00:00:00"}
            for record in DEMO_MEDIA
        ]
        cursor.fetchall.return_value = []
        self.assertEqual(seed_demo_media(connection), 0)
        self.assertFalse(any(
            "INSERT INTO media" in call.args[0]
            or "UPDATE media" in call.args[0]
            for call in cursor.execute.call_args_list
        ))


if __name__ == "__main__":
    unittest.main()
