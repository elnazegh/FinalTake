
import unittest
from backend.review import Review


class TestCC63ReviewAuthorization(unittest.TestCase):

    def test_non_owner_cannot_edit_review(self):
        review = Review(1, "1", 4.5, "Original review")

        with self.assertRaises(PermissionError):
            review.edit_review(2, "Unauthorized edit")

        self.assertEqual(review.text, "Original review")

    def test_non_owner_cannot_delete_review(self):
        review = Review(1, "1", 4.5, "Original review")

        with self.assertRaises(PermissionError):
            review.delete_review(2)

        self.assertEqual(review.text, "Original review")

    def test_owner_can_edit_review(self):
        review = Review(1, "1", 4.5, "Original review")

        review.edit_review(1, "Updated review")

        self.assertEqual(review.text, "Updated review")


if __name__ == "__main__":
    unittest.main()
