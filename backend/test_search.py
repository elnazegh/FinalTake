import unittest
from unittest.mock import MagicMock, patch

from app import app


DARK_RESULTS = [
    {
        "id": "1",
        "title": "The Dark Knight",
        "type": "movie",
        "genre": "Action",
        "imageUrl": None,
        "releaseYear": 2008,
        "description": None
    },
    {
        "id": "2",
        "title": "Dark",
        "type": "tv",
        "genre": "Drama",
        "imageUrl": None,
        "releaseYear": 2017,
        "description": None
    }
]


class SearchApiTests(unittest.TestCase):

    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

        connection_patcher = patch("app.get_db_connection")
        self.mock_get_db_connection = connection_patcher.start()
        self.addCleanup(connection_patcher.stop)

        self.connection = MagicMock()
        self.mock_get_db_connection.return_value = self.connection

        search_patcher = patch("app.search_media")
        self.mock_search_media = search_patcher.start()
        self.addCleanup(search_patcher.stop)

        self.mock_search_media.return_value = DARK_RESULTS

    def test_search_reads_from_database_catalog(self):
        response = self.client.get(
            "/api/search",
            query_string={"query": "dark"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(),
            {"results": DARK_RESULTS}
        )
        self.mock_search_media.assert_called_once_with(
            self.connection,
            "dark",
            "",
            "",
            ""
        )
        self.connection.close.assert_called_once()

    def test_no_match(self):
        self.mock_search_media.return_value = []

        response = self.client.get(
            "/api/search",
            query_string={"query": "xyz"}
        )

        self.assertEqual(
            response.get_json(),
            {"results": []}
        )

    def test_whitespace_is_trimmed(self):
        self.client.get(
            "/api/search",
            query_string={"query": "   dark   "}
        )

        self.assertEqual(
            self.mock_search_media.call_args[0][1],
            "dark"
        )

    def test_missing_query(self):
        response = self.client.get("/api/search")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(),
            {"results": []}
        )
        self.mock_get_db_connection.assert_not_called()
        self.mock_search_media.assert_not_called()

    def test_blank_query_does_not_hit_database(self):
        response = self.client.get(
            "/api/search",
            query_string={"query": "   "}
        )

        self.assertEqual(
            response.get_json(),
            {"results": []}
        )
        self.mock_get_db_connection.assert_not_called()

    def test_result_structure(self):
        response = self.client.get(
            "/api/search",
            query_string={"query": "dark"}
        )

        result = response.get_json()["results"][0]

        self.assertIn("id", result)
        self.assertIn("title", result)
        self.assertIn("type", result)
        self.assertIn("imageUrl", result)
        self.assertIn("releaseYear", result)

    def test_search_passes_filters_and_sort(self):
        response = self.client.get(
            "/api/search",
            query_string={
                "query": "dark",
                "genre": " Drama ",
                "media_type": "movie",
                "sort": "year_desc"
            }
        )

        self.assertEqual(response.status_code, 200)
        self.mock_search_media.assert_called_once_with(
            self.connection,
            "dark",
            "Drama",
            "movie",
            "year_desc"
        )

    def test_search_returns_500_when_database_unavailable(self):
        self.mock_get_db_connection.side_effect = Exception("down")

        response = self.client.get(
            "/api/search",
            query_string={"query": "dark"}
        )

        self.assertEqual(response.status_code, 500)
        self.assertIn("error", response.get_json())

    def test_search_returns_500_and_closes_connection_on_query_error(self):
        self.mock_search_media.side_effect = Exception("bad query")

        response = self.client.get(
            "/api/search",
            query_string={"query": "dark"}
        )

        self.assertEqual(response.status_code, 500)
        self.connection.close.assert_called_once()

    def test_media_details_returns_object_without_wrapper(self):
        with patch("app.get_media") as mock_get_media:
            mock_get_media.return_value = DARK_RESULTS[0]

            response = self.client.get("/api/media/1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), DARK_RESULTS[0])

    def test_media_details_not_found(self):
        with patch("app.get_media") as mock_get_media:
            mock_get_media.return_value = None

            response = self.client.get("/api/media/999")

        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
