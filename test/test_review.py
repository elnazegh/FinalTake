import unittest

from backend.review import Review


class TestReviewCharacterLimit(unittest.TestCase):

    def test_review_below_5000_characters_is_valid(self):
        text = "a" * 4999

        review = Review(
            user_id=1,
            media_id=101,
            rating=4.5,
            text=text
        )

        self.assertEqual(len(review.text), 4999)

    def test_5000_characters_is_valid(self):
        text = "a" * 5000

        review = Review(
            user_id=1,
            media_id=101,
            rating=4.5,
            text=text
        )

        self.assertEqual(len(review.text), 5000)

    def test_5001_characters_is_invalid(self):
        text = "a" * 5001

        with self.assertRaises(ValueError):
            Review(
                user_id=1,
                media_id=101,
                rating=4.5,
                text=text
            )


class TestReviewEditingAndDeletion(unittest.TestCase):

    def test_edit_review(self):
        review = Review(
            user_id=1,
            media_id=101,
            rating=4.5,
            text="Original review"
        )

        review.edit_review("Updated review")

        self.assertEqual(review.text, "Updated review")

    def test_edit_review_preserves_associations(self):
        review = Review(
            user_id=1,
            media_id=101,
            rating=4.5,
            text="Original review"
        )

        review.edit_review("Updated review")

        self.assertEqual(review.user_id, 1)
        self.assertEqual(review.media_id, 101)
        self.assertEqual(review.rating, 4.5)

    def test_edit_review_cannot_be_empty(self):
        review = Review(
            user_id=1,
            media_id=101,
            rating=4.5,
            text="Original review"
        )

        with self.assertRaises(ValueError):
            review.edit_review("")

    def test_edit_review_cannot_exceed_5000_characters(self):
        review = Review(
            user_id=1,
            media_id=101,
            rating=4.5,
            text="Original review"
        )

        with self.assertRaises(ValueError):
            review.edit_review("a" * 5001)

    def test_delete_review(self):
        review = Review(
            user_id=1,
            media_id=101,
            rating=4.5,
            text="Review to delete"
        )

        review.delete_review()

        self.assertIsNone(review.text)


class TestReviewDisplay(unittest.TestCase):

    def test_review_to_dict(self):
        review = Review(
            user_id=1,
            media_id=101,
            rating=4.5,
            text="Great movie."
        )

        review_data = review.to_dict()

        self.assertEqual(review_data["user_id"], 1)
        self.assertEqual(review_data["media_id"], 101)
        self.assertEqual(review_data["rating"], 4.5)
        self.assertEqual(review_data["text"], "Great movie.")

    def test_deleted_review_has_no_display_data(self):
        review = Review(
            user_id=1,
            media_id=101,
            rating=4.5,
            text="Great movie."
        )

        review.delete_review()

        self.assertIsNone(review.to_dict())


if __name__ == "__main__":
    unittest.main()