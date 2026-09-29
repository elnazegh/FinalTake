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


if __name__ == "__main__":
    unittest.main()
