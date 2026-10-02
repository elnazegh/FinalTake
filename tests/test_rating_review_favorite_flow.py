import unittest

from backend.rating import Rating
from backend.review import Review
from backend.favorite import Favorites


class TestRatingReviewFavoriteFlow(unittest.TestCase):

    def setUp(self):
        self.user_id = 1
        self.media_id = 101

        self.rating = Rating(
            self.user_id,
            self.media_id
        )

        self.favorites = Favorites(
            self.user_id
        )

    def test_complete_rating_review_favorite_flow(self):
        self.rating.set_rating(4.5)

        review = Review(
            user_id=self.user_id,
            media_id=self.media_id,
            rating=self.rating.value,
            text="Great movie."
        )

        favorite_added = self.favorites.add_favorite(
            self.media_id
        )

        self.assertEqual(
            self.rating.value,
            4.5
        )

        self.assertEqual(
            review.rating,
            4.5
        )

        self.assertEqual(
            review.user_id,
            self.user_id
        )

        self.assertEqual(
            review.media_id,
            self.media_id
        )

        self.assertTrue(favorite_added)

        self.assertTrue(
            self.favorites.is_favorited(
                self.media_id
            )
        )

    def test_editing_review_does_not_change_rating_or_favorite(self):
        self.rating.set_rating(4.5)

        review = Review(
            user_id=self.user_id,
            media_id=self.media_id,
            rating=self.rating.value,
            text="Original review."
        )

        self.favorites.add_favorite(
            self.media_id
        )

        review.edit_review(
            user_id=self.user_id,
            new_text="Updated review."
        )

        self.assertEqual(
            review.text,
            "Updated review."
        )

        self.assertEqual(
            self.rating.value,
            4.5
        )

        self.assertTrue(
            self.favorites.is_favorited(
                self.media_id
            )
        )

    def test_removing_favorite_does_not_change_rating_or_review(self):
        self.rating.set_rating(4.0)

        review = Review(
            user_id=self.user_id,
            media_id=self.media_id,
            rating=self.rating.value,
            text="Good movie."
        )

        self.favorites.add_favorite(
            self.media_id
        )

        self.favorites.remove_favorite(
            self.media_id
        )

        self.assertFalse(
            self.favorites.is_favorited(
                self.media_id
            )
        )

        self.assertEqual(
            self.rating.value,
            4.0
        )

        self.assertEqual(
            review.text,
            "Good movie."
        )

    def test_deleting_review_does_not_delete_rating_or_favorite(self):
        self.rating.set_rating(4.5)

        review = Review(
            user_id=self.user_id,
            media_id=self.media_id,
            rating=self.rating.value,
            text="Review to delete."
        )

        self.favorites.add_favorite(
            self.media_id
        )

        review.delete_review(
            user_id=self.user_id
        )

        self.assertIsNone(
            review.text
        )

        self.assertEqual(
            self.rating.value,
            4.5
        )

        self.assertTrue(
            self.favorites.is_favorited(
                self.media_id
            )
        )

    def test_different_users_keep_separate_favorites(self):
        user_one_favorites = Favorites(
            user_id=1
        )

        user_two_favorites = Favorites(
            user_id=2
        )

        user_one_favorites.add_favorite(
            self.media_id
        )

        self.assertTrue(
            user_one_favorites.is_favorited(
                self.media_id
            )
        )

        self.assertFalse(
            user_two_favorites.is_favorited(
                self.media_id
            )
        )


if __name__ == "__main__":
    unittest.main()