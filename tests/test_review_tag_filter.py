
"""FC4G6-74: Filter and browse reviews by their normalized tags."""

import unittest

from backend import app as app_module
from backend.review import Review


class ReviewTagFilterTests(unittest.TestCase):

    def setUp(self):
        app_module.app.config.update(TESTING=True)
        self.client = app_module.app.test_client()

        app_module.reviews.clear()
        app_module.next_review_id = 1

        app_module.reviews[1] = Review(
            1, "1", 4.5, "Drama review",
            tags="Drama, Sci Fi"
        )

        app_module.reviews[2] = Review(
            2, "2", 4.0, "Another drama",
            tags="DRAMA"
        )

        app_module.reviews[3] = Review(
            3, "1", 3.5, "Comedy review",
            tags="Comedy"
        )

        app_module.reviews[4] = Review(
            4, "2", 5.0, "No tag review"
        )

    def tearDown(self):
        app_module.reviews.clear()
        app_module.next_review_id = 1

    def get_filtered(self, **filters):
        response = self.client.get(
            "/api/reviews",
            query_string=filters
        )

        self.assertEqual(
            response.status_code,
            200
        )

        return response.get_json()["reviews"]

    def test_no_filter_returns_all_reviews(self):
        self.assertEqual(
            len(self.get_filtered()),
            4
        )

    def test_tag_filter_matches_without_case_sensitivity(self):
        results = self.get_filtered(tag="dRaMa")

        self.assertEqual(
            [review["id"] for review in results],
            [1, 2]
        )

    def test_multiword_tag_normalizes_whitespace(self):
        results = self.get_filtered(
            tag="  SCI   FI  "
        )

        self.assertEqual(
            [review["id"] for review in results],
            [1]
        )

    def test_filter_uses_exact_tags_not_substrings(self):
        results = self.get_filtered(tag="sci")

        self.assertEqual(results, [])

    def test_unknown_tag_returns_empty_list(self):
        results = self.get_filtered(tag="history")

        self.assertEqual(results, [])

    def test_filter_and_media_id_work_together(self):
        results = self.get_filtered(
            tag="drama",
            media_id="1"
        )

        self.assertEqual(
            [review["id"] for review in results],
            [1]
        )

    def test_filter_preserves_review_response_fields(self):
        results = self.get_filtered(tag="drama")

        self.assertEqual(
            results[0]["tags"],
            ["drama", "sci fi"]
        )

        self.assertEqual(
            results[0]["media_title"],
            "The Dark Knight"
        )

        self.assertEqual(
            results[0]["text"],
            "Drama review"
        )

    def test_empty_tag_filter_is_rejected(self):
        response = self.client.get(
            "/api/reviews",
            query_string={"tag": "  "}
        )

        self.assertEqual(
            response.status_code,
            400
        )

        self.assertIn(
            "error",
            response.get_json()
        )

    def test_multiple_tags_in_one_filter_are_rejected(self):
        response = self.client.get(
            "/api/reviews",
            query_string={
                "tag": "drama, comedy"
            }
        )

        self.assertEqual(
            response.status_code,
            400
        )

    def test_deletion_removes_review_from_tag_results(self):
        app_module.reviews[1].delete_review(1)

        results = self.get_filtered(tag="drama")

        self.assertEqual(
            [review["id"] for review in results],
            [2]
        )

    def test_tag_edit_updates_filter_results(self):
        app_module.reviews[3].edit_tags(
            3,
            "Drama"
        )

        results = self.get_filtered(tag="drama")

        self.assertEqual(
            [review["id"] for review in results],
            [1, 2, 3]
        )


if __name__ == "__main__":
    unittest.main()
