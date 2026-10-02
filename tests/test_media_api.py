import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

from backend import app as app_module


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
        self.assertEqual(
            response.get_json()["media"]["title"],
            "Interstellar"
        )

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


if __name__ == "__main__":
    unittest.main()
