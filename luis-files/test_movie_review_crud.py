import unittest

import movie_review_crud as crud


class TestMovieReviewCrud(unittest.TestCase):

    def setUp(self):
        crud.reviews.clear()
        crud._next_id = 1

    def test_create_review(self):
        review = crud.create_review("Inception", 5, "Great movie")

        self.assertEqual(review["id"], 1)
        self.assertEqual(review["movie_title"], "Inception")
        self.assertEqual(review["rating"], 5)
        self.assertEqual(review["comment"], "Great movie")

    def test_create_review_assigns_unique_ids(self):
        first = crud.create_review("Inception", 5)
        second = crud.create_review("Memento", 4)

        self.assertNotEqual(first["id"], second["id"])

    def test_create_review_defaults_to_empty_comment(self):
        review = crud.create_review("Inception", 5)

        self.assertEqual(review["comment"], "")

    def test_get_review(self):
        created = crud.create_review("Inception", 5)

        self.assertEqual(crud.get_review(created["id"]), created)

    def test_get_review_missing_returns_none(self):
        self.assertIsNone(crud.get_review(999))

    def test_list_reviews_empty(self):
        self.assertEqual(crud.list_reviews(), [])

    def test_list_reviews_returns_all(self):
        crud.create_review("Inception", 5)
        crud.create_review("Memento", 4)

        self.assertEqual(len(crud.list_reviews()), 2)

    def test_update_review_rating_and_comment(self):
        created = crud.create_review("Inception", 5, "Great movie")

        updated = crud.update_review(created["id"], rating=4, comment="Still great")

        self.assertEqual(updated["rating"], 4)
        self.assertEqual(updated["comment"], "Still great")

    def test_update_review_partial_preserves_other_fields(self):
        created = crud.create_review("Inception", 5, "Great movie")

        updated = crud.update_review(created["id"], rating=3)

        self.assertEqual(updated["rating"], 3)
        self.assertEqual(updated["comment"], "Great movie")
        self.assertEqual(updated["movie_title"], "Inception")

    def test_update_review_missing_returns_none(self):
        self.assertIsNone(crud.update_review(999, rating=3))

    def test_delete_review(self):
        created = crud.create_review("Inception", 5)

        self.assertTrue(crud.delete_review(created["id"]))
        self.assertIsNone(crud.get_review(created["id"]))

    def test_delete_review_missing_returns_false(self):
        self.assertFalse(crud.delete_review(999))


if __name__ == "__main__":
    unittest.main()
