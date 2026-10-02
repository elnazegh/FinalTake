import unittest
from app import app


class SearchApiTests(unittest.TestCase):

    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_partial_title_match(self):
        response = self.client.get(
            "/api/search",
            query_string={"query": "dark"}
        )

        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        titles = [item["title"] for item in data["results"]]

        self.assertIn("The Dark Knight", titles)
        self.assertIn("Dark", titles)
        self.assertIn("Darkest Hour", titles)
        self.assertIn("Dark Souls", titles)

    def test_case_insensitive_search(self):
        lower = self.client.get(
            "/api/search",
            query_string={"query": "dark"}
        ).get_json()

        upper = self.client.get(
            "/api/search",
            query_string={"query": "DARK"}
        ).get_json()

        self.assertEqual(lower, upper)

    def test_middle_title_match(self):
        response = self.client.get(
            "/api/search",
            query_string={"query": "souls"}
        )

        data = response.get_json()
        titles = [item["title"] for item in data["results"]]

        self.assertIn("Dark Souls", titles)

    def test_no_match(self):
        response = self.client.get(
            "/api/search",
            query_string={"query": "xyz"}
        )

        self.assertEqual(
            response.get_json(),
            {"results": []}
        )

    def test_whitespace_is_trimmed(self):
        normal = self.client.get(
            "/api/search",
            query_string={"query": "dark"}
        ).get_json()

        spaced = self.client.get(
            "/api/search",
            query_string={"query": "   dark   "}
        ).get_json()

        self.assertEqual(normal, spaced)

    def test_missing_query(self):
        response = self.client.get("/api/search")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(),
            {"results": []}
        )

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

    def test_search_filters_by_genre(self):
        response = self.client.get(
            "/api/search",
            query_string={
                "query": "dark",
                "genre": "Drama"
            }
        )

        self.assertEqual(response.status_code, 200)

        results = response.get_json()["results"]
        titles = [item["title"] for item in results]

        self.assertEqual(
            titles,
            ["Dark", "Darkest Hour"]
        )

        for item in results:
            self.assertEqual(item["genre"], "Drama")

    def test_search_filters_by_media_type(self):
        response = self.client.get(
            "/api/search",
            query_string={
                "query": "dark",
                "media_type": "movie"
            }
        )

        self.assertEqual(response.status_code, 200)

        results = response.get_json()["results"]
        titles = [item["title"] for item in results]

        self.assertEqual(
            titles,
            ["The Dark Knight", "Darkest Hour"]
        )

        for item in results:
            self.assertEqual(item["type"], "movie")

    def test_search_combines_genre_and_media_type(self):
        response = self.client.get(
            "/api/search",
            query_string={
                "query": "dark",
                "genre": "Drama",
                "media_type": "movie"
            }
        )

        self.assertEqual(response.status_code, 200)

        results = response.get_json()["results"]

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Darkest Hour")
        self.assertEqual(results[0]["genre"], "Drama")
        self.assertEqual(results[0]["type"], "movie")

    def test_search_combined_filters_no_match(self):
        response = self.client.get(
            "/api/search",
            query_string={
                "query": "dark",
                "genre": "RPG",
                "media_type": "movie"
            }
        )

        self.assertEqual(response.status_code, 200)

        results = response.get_json()["results"]

        self.assertEqual(results, [])

    def test_search_sorts_title_ascending(self):
        response = self.client.get(
            "/api/search",
            query_string={
                "query": "dark",
                "sort": "title_asc"
            }
        )

        self.assertEqual(response.status_code, 200)

        results = response.get_json()["results"]
        titles = [item["title"] for item in results]

        self.assertEqual(
            titles,
            sorted(titles, key=str.casefold)
        )

    def test_search_sorts_year_newest_first(self):
        response = self.client.get(
            "/api/search",
            query_string={
                "query": "dark",
                "sort": "year_desc"
            }
        )

        self.assertEqual(response.status_code, 200)

        results = response.get_json()["results"]
        years = [item["releaseYear"] for item in results]

        self.assertEqual(
            years,
            sorted(years, reverse=True)
        )


if __name__ == "__main__":
    unittest.main()
