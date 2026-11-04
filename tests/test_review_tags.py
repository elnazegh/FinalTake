
"""FC4G6-72: Review tag normalization, validation, and ownership tests."""

import unittest

from backend.review import Review
from backend.tag import normalize_tags


class TestTagNormalization(unittest.TestCase):

    def test_normalizes_case_spacing_and_duplicates(self):
        self.assertEqual(
            normalize_tags("Sci Fi, sci  fi, DRAMA"),
            ["sci fi", "drama"]
        )

    def test_optional_empty_tags(self):
        self.assertEqual(normalize_tags(None), [])
        self.assertEqual(normalize_tags(""), [])
        self.assertEqual(normalize_tags([]), [])

    def test_invalid_empty_tag_is_rejected(self):
        with self.assertRaises(ValueError):
            normalize_tags("Drama,,Comedy")

    def test_invalid_type_is_rejected(self):
        with self.assertRaises(ValueError):
            normalize_tags(["Drama", 123])

    def test_list_item_with_comma_is_rejected(self):
        with self.assertRaises(ValueError):
            normalize_tags(["Drama, Comedy"])


class TestReviewTags(unittest.TestCase):

    def test_new_review_normalizes_tags(self):
        review = Review(
            1, 101, 4.5, "Good movie",
            "Sci Fi, sci fi"
        )
        self.assertEqual(review.tags, ["sci fi"])

    def test_text_only_review_can_reach_5000_characters(self):
        review = Review(1, 101, 4.5, "x" * 5000)
        self.assertEqual(len(review.text), 5000)

    def test_combined_limit_rejects_creation(self):
        with self.assertRaises(ValueError):
            Review(1, 101, 4.5, "x" * 5000, "comedy")

    def test_combined_limit_counts_tag_separators(self):
        review = Review(
            1, 101, 4.5, "x" * 4993, "art, tv"
        )
        self.assertEqual(review.tags, ["art", "tv"])

        with self.assertRaises(ValueError):
            Review(1, 101, 4.5, "x" * 4994, "art, tv")

    def test_invalid_text_edit_preserves_previous_text(self):
        review = Review(
            1, 101, 4.5, "Original", "comedy"
        )

        with self.assertRaises(ValueError):
            review.edit_review(1, "x" * 5000)

        self.assertEqual(review.text, "Original")
        self.assertEqual(review.tags, ["comedy"])

    def test_invalid_tag_edit_preserves_previous_tags(self):
        review = Review(
            1, 101, 4.5, "x" * 4995, "art"
        )

        with self.assertRaises(ValueError):
            review.edit_tags(1, "comedy")

        self.assertEqual(review.tags, ["art"])

    def test_owner_can_replace_tags(self):
        review = Review(
            1, 101, 4.5, "Good movie", "art"
        )
        review.edit_tags(1, "Comedy, Drama")

        self.assertEqual(
            review.tags, ["comedy", "drama"]
        )

    def test_non_owner_cannot_edit_tags(self):
        review = Review(
            1, 101, 4.5, "Good movie", "art"
        )

        with self.assertRaises(PermissionError):
            review.edit_tags(2, "comedy")

        self.assertEqual(review.tags, ["art"])

    def test_deleted_review_tags_cannot_be_modified(self):
        review = Review(
            1, 101, 4.5, "Good movie", "art"
        )
        review.delete_review(1)

        with self.assertRaises(ValueError):
            review.edit_tags(1, "comedy")

        self.assertEqual(review.tags, ["art"])

    def test_returned_tag_list_cannot_mutate_review(self):
        review = Review(
            1, 101, 4.5, "Good movie", "art"
        )

        review.tags.append("injected")
        self.assertEqual(review.tags, ["art"])

        with self.assertRaises(AttributeError):
            review.tags = ["injected"]


if __name__ == "__main__":
    unittest.main()
