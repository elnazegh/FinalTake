import unittest
from unittest.mock import MagicMock, patch

from app import app, get_media_by_id, load_media_titles
from media import get_media, list_media, search_media
from seed_media import MediaSeedConflict, seed_demo_media


def media_row(media_id=7):
    return {
        "media_id": media_id,
        "title": "Arrival",
        "media_type": "movie",
        "genre": "Science Fiction",
        "image_url": "https://example.com/arrival.jpg",
        "release_year": 2016,
        "description": "First contact story."
    }


class MediaReadHelperTests(unittest.TestCase):

    def setUp(self):
        self.connection = MagicMock()
        self.cursor = MagicMock()
        self.connection.cursor.return_value = self.cursor

    def test_list_media_uses_dictionary_cursor_and_serializes_fields(self):
        self.cursor.fetchall.return_value = [media_row()]

        result = list_media(self.connection)

        self.connection.cursor.assert_called_once_with(dictionary=True)
        self.assertEqual(result, [{
            "id": "7",
            "title": "Arrival",
            "type": "movie",
            "genre": "Science Fiction",
            "imageUrl": "https://example.com/arrival.jpg",
            "releaseYear": 2016,
            "description": "First contact story."
        }])
        self.cursor.close.assert_called_once()

    def test_get_media_parameterizes_id_and_serializes_record(self):
        self.cursor.fetchone.return_value = media_row()

        result = get_media(self.connection, "7")

        self.cursor.execute.assert_called_once()
        query, parameters = self.cursor.execute.call_args.args
        self.assertIn("WHERE media_id = %s", query)
        self.assertEqual(parameters, (7,))
        self.assertEqual(result["id"], "7")

    def test_get_media_rejects_invalid_ids_without_querying(self):
        for value in (True, 0, -1, "7 OR 1=1", "７"):
            with self.subTest(value=value):
                self.assertIsNone(get_media(self.connection, value))

        self.connection.cursor.assert_not_called()

    def test_search_uses_parameterized_filters_and_allowlisted_sort(self):
        self.cursor.fetchall.return_value = [media_row()]

        result = search_media(
            self.connection,
            "dark%_!",
            genre="Drama",
            media_type="movie",
            sort="title_asc"
        )

        query, parameters = self.cursor.execute.call_args.args
        self.assertIn("LOWER(title) LIKE LOWER(%s)", query)
        self.assertIn("LOWER(genre) = LOWER(%s)", query)
        self.assertIn("LOWER(media_type) = LOWER(%s)", query)
        self.assertIn("ORDER BY title ASC, media_id ASC", query)
        self.assertEqual(
            parameters,
            ("%dark!%!_!!%", "Drama", "movie")
        )
        self.assertNotIn("dark%_!", query)
        self.assertEqual(result[0]["id"], "7")

    def test_search_rejects_sort_sql_injection_by_using_default(self):
        self.cursor.fetchall.return_value = []

        search_media(
            self.connection,
            "dark",
            sort="title_asc; DROP TABLE media"
        )

        query = self.cursor.execute.call_args.args[0]
        self.assertIn("ORDER BY media_id ASC", query)
        self.assertNotIn("DROP TABLE", query)

    def test_search_supports_all_existing_sort_options(self):
        expected_orders = {
            "title_asc": "title ASC, media_id ASC",
            "title_desc": "title DESC, media_id ASC",
            "year_asc": "release_year ASC",
            "year_desc": "release_year DESC"
        }

        for sort, expected_order in expected_orders.items():
            with self.subTest(sort=sort):
                search_media(self.connection, "dark", sort=sort)
                query = self.cursor.execute.call_args.args[0]
                self.assertIn(f"ORDER BY {expected_order}", query)


class MediaReadApiTests(unittest.TestCase):

    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def mock_connection(self):
        connection = MagicMock()
        cursor = MagicMock()
        connection.cursor.return_value = cursor
        return connection, cursor

    @patch("app.get_db_connection")
    def test_get_media_catalog(self, mock_get_db_connection):
        connection, cursor = self.mock_connection()
        cursor.fetchall.return_value = [media_row()]
        mock_get_db_connection.return_value = connection

        response = self.client.get("/api/media")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["media"][0]["id"], "7")
        self.assertEqual(response.get_json()["media"][0]["type"], "movie")
        connection.close.assert_called_once()

    @patch("app.get_db_connection")
    def test_get_media_details_returns_direct_object(self, mock_get_db_connection):
        connection, cursor = self.mock_connection()
        cursor.fetchone.return_value = media_row()
        mock_get_db_connection.return_value = connection

        response = self.client.get("/api/media/7")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["id"], "7")
        self.assertNotIn("media", response.get_json())
        connection.close.assert_called_once()

    @patch("app.get_db_connection")
    def test_get_media_details_returns_404_for_missing_id(
        self, mock_get_db_connection
    ):
        connection, cursor = self.mock_connection()
        cursor.fetchone.return_value = None
        mock_get_db_connection.return_value = connection

        response = self.client.get("/api/media/999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json(), {"error": "Media not found."})

    @patch("app.get_db_connection")
    def test_search_returns_existing_response_shape(self, mock_get_db_connection):
        connection, cursor = self.mock_connection()
        cursor.fetchall.return_value = [media_row()]
        mock_get_db_connection.return_value = connection

        response = self.client.get(
            "/api/search",
            query_string={
                "query": "arrival",
                "genre": "Science Fiction",
                "media_type": "movie",
                "sort": "year_desc"
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["results"][0]["id"], "7")
        query, parameters = cursor.execute.call_args.args
        self.assertIn("ORDER BY release_year DESC", query)
        self.assertEqual(
            parameters,
            ("%arrival%", "Science Fiction", "movie")
        )

    @patch("app.get_db_connection")
    def test_search_special_input_is_passed_as_parameter(
        self, mock_get_db_connection
    ):
        connection, cursor = self.mock_connection()
        cursor.fetchall.return_value = []
        mock_get_db_connection.return_value = connection
        query_text = "' OR 1=1 --"

        response = self.client.get(
            "/api/search",
            query_string={"query": query_text}
        )

        self.assertEqual(response.status_code, 200)
        query, parameters = cursor.execute.call_args.args
        self.assertNotIn(query_text, query)
        self.assertEqual(parameters, (f"%{query_text}%",))

    @patch("app.get_db_connection")
    def test_database_failures_are_generic(self, mock_get_db_connection):
        mock_get_db_connection.side_effect = RuntimeError(
            "private database detail"
        )

        for path in ("/api/media", "/api/media/7", "/api/search?query=a"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 500)
                self.assertNotIn(
                    "private database detail",
                    response.get_data(as_text=True)
                )

    @patch("app.get_db_connection")
    def test_review_lookup_uses_mysql_media(self, mock_get_db_connection):
        connection, cursor = self.mock_connection()
        cursor.fetchone.return_value = media_row()
        mock_get_db_connection.return_value = connection

        result = get_media_by_id("7")

        self.assertEqual(result["title"], "Arrival")
        connection.close.assert_called_once()

    @patch("app.get_db_connection")
    def test_review_title_lookup_uses_one_connection(
        self, mock_get_db_connection
    ):
        connection, cursor = self.mock_connection()
        cursor.fetchone.side_effect = [
            media_row(1),
            {
                **media_row(4),
                "title": "Dune",
                "media_type": "book"
            }
        ]
        mock_get_db_connection.return_value = connection

        titles = load_media_titles(["1", "4", "1"])

        self.assertEqual(titles, {"1": "Arrival", "4": "Dune"})
        self.assertEqual(connection.cursor.call_count, 2)
        connection.close.assert_called_once()

    def test_empty_search_does_not_connect(self):
        with patch("app.get_db_connection") as mock_get_db_connection:
            response = self.client.get("/api/search")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"results": []})
        mock_get_db_connection.assert_not_called()


class DemoMediaSeedUnitTests(unittest.TestCase):

    def test_conflicting_id_fails_before_any_insert(self):
        connection = MagicMock()
        cursor = MagicMock()
        connection.cursor.return_value = cursor
        cursor.fetchone.side_effect = [
            {
                "media_id": 1,
                "title": "Different media",
                "media_type": "movie",
                "genre": None,
                "image_url": None,
                "release_year": None,
                "description": None
            },
            None,
            None,
            None,
            None
        ]
        cursor.fetchall.return_value = []

        with self.assertRaisesRegex(MediaSeedConflict, "ID 1 is occupied"):
            seed_demo_media(connection)

        self.assertFalse(any(
            "INSERT INTO media" in call.args[0]
            for call in cursor.execute.call_args_list
        ))
        connection.commit.assert_not_called()
        connection.rollback.assert_called_once()
        cursor.close.assert_called_once()

    def test_existing_demo_title_under_another_id_is_reported(self):
        connection = MagicMock()
        cursor = MagicMock()
        connection.cursor.return_value = cursor
        cursor.fetchone.return_value = None
        cursor.fetchall.side_effect = [
            [{"media_id": 99}],
            [],
            [],
            [],
            []
        ]

        with self.assertRaisesRegex(MediaSeedConflict, "under ID\\(s\\) 99"):
            seed_demo_media(connection)

        self.assertFalse(any(
            "INSERT INTO media" in call.args[0]
            for call in cursor.execute.call_args_list
        ))
        connection.commit.assert_not_called()
        connection.rollback.assert_called_once()


if __name__ == "__main__":
    unittest.main()
