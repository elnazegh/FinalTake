"""FC4G6-21: verify every searchable catalog field is present and queryable."""

import unittest

import app as app_module
from app import app

SEARCHABLE_FIELDS = {
    "id": str,
    "title": str,
    "type": str,
    "genre": str,
    "releaseYear": int,
}
SORT_KEYS = ("title_asc", "title_desc", "year_asc", "year_desc")


class SearchableFieldTests(unittest.TestCase):

    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def search(self, **params):
        response = self.client.get("/api/search", query_string=params)

        self.assertEqual(response.status_code, 200)

        return response.get_json()["results"]

    def test_every_item_has_each_searchable_field_with_a_valid_value(self):
        for media in app_module.media_items:
            for field, expected_type in SEARCHABLE_FIELDS.items():
                with self.subTest(media_id=media["id"], field=field):
                    self.assertIn(field, media)
                    self.assertIsInstance(media[field], expected_type)

                    if expected_type is str:
                        self.assertTrue(media[field].strip())

    def test_image_url_field_exists_on_every_item(self):
        for media in app_module.media_items:
            with self.subTest(media_id=media["id"]):
                self.assertIn("imageUrl", media)

    def test_every_item_is_found_by_its_exact_title(self):
        for media in app_module.media_items:
            with self.subTest(title=media["title"]):
                ids = [item["id"] for item in self.search(query=media["title"])]

                self.assertIn(media["id"], ids)

    def test_every_item_is_found_by_a_partial_title(self):
        for media in app_module.media_items:
            with self.subTest(title=media["title"]):
                partial = media["title"][1:-1] or media["title"]
                ids = [item["id"] for item in self.search(query=partial)]

                self.assertIn(media["id"], ids)

    def test_title_search_ignores_case(self):
        for media in app_module.media_items:
            with self.subTest(title=media["title"]):
                ids = [
                    item["id"]
                    for item in self.search(query=media["title"].upper())
                ]

                self.assertIn(media["id"], ids)

    def test_every_item_is_found_by_its_genre_filter(self):
        for media in app_module.media_items:
            with self.subTest(media_id=media["id"], genre=media["genre"]):
                results = self.search(query=media["title"], genre=media["genre"])

                self.assertIn(media["id"], [item["id"] for item in results])
                self.assertTrue(
                    all(item["genre"] == media["genre"] for item in results)
                )

    def test_every_item_is_found_by_its_type_filter(self):
        for media in app_module.media_items:
            with self.subTest(media_id=media["id"], type=media["type"]):
                results = self.search(
                    query=media["title"], media_type=media["type"]
                )

                self.assertIn(media["id"], [item["id"] for item in results])
                self.assertTrue(
                    all(item["type"] == media["type"] for item in results)
                )

    def test_wrong_genre_and_type_filters_exclude_each_item(self):
        for media in app_module.media_items:
            with self.subTest(media_id=media["id"]):
                self.assertEqual(
                    self.search(query=media["title"], genre="No Such Genre"), []
                )
                self.assertEqual(
                    self.search(query=media["title"], media_type="nosuchtype"), []
                )

    def test_search_results_expose_every_searchable_field(self):
        for media in app_module.media_items:
            with self.subTest(title=media["title"]):
                result = next(
                    item
                    for item in self.search(query=media["title"])
                    if item["id"] == media["id"]
                )

                for field in SEARCHABLE_FIELDS:
                    self.assertEqual(result[field], media[field])

    def test_every_sort_option_keeps_all_matching_items(self):
        expected = sorted(item["id"] for item in self.search(query="d"))

        for sort in SORT_KEYS:
            with self.subTest(sort=sort):
                ids = sorted(item["id"] for item in self.search(query="d", sort=sort))

                self.assertEqual(ids, expected)


if __name__ == "__main__":
    unittest.main()
