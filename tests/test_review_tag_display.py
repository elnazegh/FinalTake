
"""FC4G6-73: Review tag storage and display representation tests."""

import unittest

from backend.review import Review


class TestReviewTagDisplay(unittest.TestCase):

    def test_review_without_tags_displays_empty_list(self):
        review = Review(1, 101, 4.5, "Good movie")
        self.assertEqual(review.to_dict()["tags"], [])

    def test_review_displays_normalized_unique_tags(self):
        review = Review(
            1, 101, 4.5, "Good movie",
            "Sci Fi, Drama, sci fi"
        )
        self.assertEqual(
            review.to_dict()["tags"],
            ["sci fi", "drama"]
        )

    def test_text_edit_preserves_displayed_tags(self):
        review = Review(
            1, 101, 4.5, "Original review", "Drama"
        )
        review.edit_review(1, "Updated review")

        self.assertEqual(
            review.to_dict()["text"],
            "Updated review"
        )
        self.assertEqual(
            review.to_dict()["tags"],
            ["drama"]
        )

    def test_tag_edit_updates_displayed_tags(self):
        review = Review(
            1, 101, 4.5, "Good movie", "Drama"
        )
        review.edit_tags(1, ["Comedy", "Drama"])

        self.assertEqual(
            review.to_dict()["tags"],
            ["comedy", "drama"]
        )

    def test_to_dict_includes_unchanged_review_fields(self):
        review = Review(
            7, 202, 3.5, "Interesting book", "Fantasy"
        )
        self.assertEqual(review.to_dict(), {
            "user_id": 7,
            "media_id": 202,
            "rating": 3.5,
            "text": "Interesting book",
            "tags": ["fantasy"],
        })

    def test_returned_tag_list_is_independent(self):
        review = Review(
            1, 101, 4.5, "Good movie", "Drama"
        )
        display_data = review.to_dict()
        display_data["tags"].append("injected")

        self.assertEqual(
            review.to_dict()["tags"],
            ["drama"]
        )

    def test_deleted_review_displays_nothing(self):
        review = Review(
            1, 101, 4.5, "Good movie", "Drama"
        )
        review.delete_review(1)

        self.assertIsNone(review.to_dict())


if __name__ == "__main__":
    unittest.main()
