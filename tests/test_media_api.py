import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

from backend import app as app_module
from backend import media as media_module


class MediaApiTests(unittest.TestCase):

    def setUp(self):
        app_module.app.config["TESTING"] = True
        self.client = app_module.app.test_client()

    def create_mock_connection(self, cursors):
        connection = MagicMock()
        connection.cursor.side_effect = cursors

        return connection

    @patch("backend.app.get_db_connection")
    def test_get_media_catalog(self, mock_get_db_connection):
        cursor = MagicMock()
        cursor.fetchall.return_value = [
            {
                "media_id": 1,
                "title": "Interstellar",
                "media_type": "movie",
                "genre": "Science Fiction",
                "image_url": None,
                "release_year": 2014,
                "description": "Space exploration drama."
            }
        ]

        mock_get_db_connection.return_value = self.create_mock_connection(
            [cursor]
        )

        response = self.client.get("/api/media")

        self.assertEqual(response.status_code, 200)

        media = response.get_json()["media"]

        self.assertEqual(media[0]["id"], "1")
        self.assertEqual(media[0]["title"], "Interstellar")
        self.assertEqual(media[0]["type"], "movie")
        self.assertEqual(media[0]["releaseYear"], 2014)

    @patch("backend.app.get_db_connection")
    def test_get_media_details(self, mock_get_db_connection):
        cursor = MagicMock()
        cursor.fetchone.return_value = {
            "media_id": 1,
            "title": "Interstellar",
            "media_type": "movie",
            "genre": "Science Fiction",
            "image_url": None,
            "release_year": 2014,
            "description": "Space exploration drama."
        }

        mock_get_db_connection.return_value = self.create_mock_connection(
            [cursor]
        )

        response = self.client.get("/api/media/1")

        self.assertEqual(response.status_code, 200)

        # Frontend expects the media object directly, not wrapped.
        body = response.get_json()

        self.assertNotIn("media", body)
        self.assertEqual(body["title"], "Interstellar")
        self.assertEqual(body["id"], "1")

    @patch("backend.app.get_db_connection")
    def test_get_media_details_not_found(self, mock_get_db_connection):
        cursor = MagicMock()
        cursor.fetchone.return_value = None

        mock_get_db_connection.return_value = self.create_mock_connection(
            [cursor]
        )

        response = self.client.get("/api/media/999")

        self.assertEqual(response.status_code, 404)

    @patch("backend.app.get_db_connection")
    def test_create_media(self, mock_get_db_connection):
        insert_cursor = MagicMock()
        insert_cursor.lastrowid = 7

        select_cursor = MagicMock()
        select_cursor.fetchone.return_value = {
            "media_id": 7,
            "title": "Arrival",
            "media_type": "movie",
            "genre": "Science Fiction",
            "image_url": None,
            "release_year": 2016,
            "description": "First contact story."
        }

        connection = self.create_mock_connection(
            [
                insert_cursor,
                select_cursor
            ]
        )
        mock_get_db_connection.return_value = connection

        response = self.client.post(
            "/api/media",
            json={
                "title": "Arrival",
                "type": "movie",
                "genre": "Science Fiction",
                "releaseYear": 2016,
                "description": "First contact story."
            }
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.get_json()["media"]["id"],
            "7"
        )
        connection.commit.assert_called_once()

    def test_create_media_requires_title(self):
        response = self.client.post(
            "/api/media",
            json={
                "type": "movie"
            }
        )

        self.assertEqual(response.status_code, 400)

    def test_create_media_requires_valid_type(self):
        response = self.client.post(
            "/api/media",
            json={
                "title": "Unknown",
                "type": "podcast"
            }
        )

        self.assertEqual(response.status_code, 400)

    def test_media_details_route_is_registered_once(self):
        rules = [
            rule
            for rule in app_module.app.url_map.iter_rules()
            if rule.rule == "/api/media/<int:media_id>"
            and "GET" in rule.methods
        ]

        self.assertEqual(len(rules), 1)

    @patch("backend.app.get_db_connection")
    def test_create_media_rejects_non_object_json(
        self,
        mock_get_db_connection
    ):
        for body in (["Arrival"], "Arrival", 7, [], None):
            with self.subTest(body=body):
                response = self.client.post(
                    "/api/media",
                    json=body
                )

                self.assertEqual(response.status_code, 400)

        mock_get_db_connection.assert_not_called()

    def test_create_media_rejects_boolean_release_year(self):
        for value in (True, False):
            with self.subTest(value=value):
                response = self.client.post(
                    "/api/media",
                    json={
                        "title": "Arrival",
                        "type": "movie",
                        "releaseYear": value
                    }
                )

                self.assertEqual(response.status_code, 400)

    def test_create_media_rejects_out_of_range_release_year(self):
        for value in (-1, 10000):
            with self.subTest(value=value):
                response = self.client.post(
                    "/api/media",
                    json={
                        "title": "Arrival",
                        "type": "movie",
                        "releaseYear": value
                    }
                )

                self.assertEqual(response.status_code, 400)

    def test_create_media_rejects_overlong_fields(self):
        limits = {
            "title": media_module.MAX_TITLE_LENGTH,
            "genre": media_module.MAX_GENRE_LENGTH,
            "imageUrl": media_module.MAX_IMAGE_URL_LENGTH,
            "description": media_module.MAX_DESCRIPTION_LENGTH
        }

        for field, limit in limits.items():
            with self.subTest(field=field):
                payload = {
                    "title": "Arrival",
                    "type": "movie"
                }
                payload[field] = "x" * (limit + 1)

                response = self.client.post(
                    "/api/media",
                    json=payload
                )

                self.assertEqual(response.status_code, 400)

    def test_validate_media_payload_accepts_max_length_fields(self):
        data = media_module.validate_media_payload({
            "title": "x" * media_module.MAX_TITLE_LENGTH,
            "type": "Movie",
            "genre": "x" * media_module.MAX_GENRE_LENGTH,
            "imageUrl": "x" * media_module.MAX_IMAGE_URL_LENGTH,
            "description": "x" * media_module.MAX_DESCRIPTION_LENGTH,
            "releaseYear": 0
        })

        self.assertEqual(data["media_type"], "movie")
        self.assertEqual(data["release_year"], 0)

    def test_create_media_rejects_non_text_optional_fields(self):
        for field in ("genre", "imageUrl", "description"):
            with self.subTest(field=field):
                response = self.client.post(
                    "/api/media",
                    json={
                        "title": "Arrival",
                        "type": "movie",
                        field: 123
                    }
                )

                self.assertEqual(response.status_code, 400)

    @patch("backend.app.get_db_connection")
    def test_create_media_does_not_commit_without_read_back(
        self,
        mock_get_db_connection
    ):
        insert_cursor = MagicMock()
        insert_cursor.lastrowid = 7

        select_cursor = MagicMock()
        select_cursor.fetchone.return_value = None

        connection = self.create_mock_connection(
            [
                insert_cursor,
                select_cursor
            ]
        )
        mock_get_db_connection.return_value = connection

        response = self.client.post(
            "/api/media",
            json={
                "title": "Arrival",
                "type": "movie"
            }
        )

        self.assertEqual(response.status_code, 500)
        connection.commit.assert_not_called()
        connection.rollback.assert_called_once()
        connection.close.assert_called_once()

    @patch("backend.app.get_db_connection")
    def test_create_media_commits_after_read_back(
        self,
        mock_get_db_connection
    ):
        calls = []

        insert_cursor = MagicMock()
        insert_cursor.lastrowid = 7

        select_cursor = MagicMock()
        select_cursor.fetchone.side_effect = lambda: (
            calls.append("read")
            or {
                "media_id": 7,
                "title": "Arrival",
                "media_type": "movie",
                "genre": None,
                "image_url": None,
                "release_year": None,
                "description": None
            }
        )

        connection = self.create_mock_connection(
            [
                insert_cursor,
                select_cursor
            ]
        )
        connection.commit.side_effect = lambda: calls.append("commit")
        mock_get_db_connection.return_value = connection

        response = self.client.post(
            "/api/media",
            json={
                "title": "Arrival",
                "type": "movie"
            }
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(calls, ["read", "commit"])
        connection.rollback.assert_not_called()

    @patch("backend.app.get_db_connection")
    def test_create_media_rolls_back_when_commit_fails(
        self,
        mock_get_db_connection
    ):
        insert_cursor = MagicMock()
        insert_cursor.lastrowid = 7

        select_cursor = MagicMock()
        select_cursor.fetchone.return_value = {
            "media_id": 7,
            "title": "Arrival",
            "media_type": "movie",
            "genre": None,
            "image_url": None,
            "release_year": None,
            "description": None
        }

        connection = self.create_mock_connection(
            [
                insert_cursor,
                select_cursor
            ]
        )
        connection.commit.side_effect = Exception("commit failed")
        mock_get_db_connection.return_value = connection

        response = self.client.post(
            "/api/media",
            json={
                "title": "Arrival",
                "type": "movie"
            }
        )

        self.assertEqual(response.status_code, 500)
        connection.rollback.assert_called_once()

    def test_search_media_escapes_like_wildcards(self):
        cursor = MagicMock()
        cursor.fetchall.return_value = []

        connection = self.create_mock_connection([cursor])

        media_module.search_media(
            connection,
            "100%_!",
            genre="Drama",
            media_type="movie",
            sort="year_desc"
        )

        sql, parameters = cursor.execute.call_args[0]

        self.assertEqual(
            parameters,
            ("%100!%!_!!%", "Drama", "movie")
        )
        self.assertIn("ORDER BY release_year DESC", sql)
        cursor.close.assert_called_once()

    def test_search_media_ignores_unknown_sort(self):
        cursor = MagicMock()
        cursor.fetchall.return_value = []

        connection = self.create_mock_connection([cursor])

        media_module.search_media(
            connection,
            "dark",
            sort="title; DROP TABLE media"
        )

        sql, _ = cursor.execute.call_args[0]

        self.assertIn("ORDER BY media_id ASC", sql)
        self.assertNotIn("DROP", sql)

    def test_get_media_rejects_invalid_ids_without_querying(self):
        connection = MagicMock()

        for value in (True, 0, -1, "abc", "1.5", None):
            with self.subTest(value=value):
                self.assertIsNone(
                    media_module.get_media(connection, value)
                )

        connection.cursor.assert_not_called()


if __name__ == "__main__":
    unittest.main()
