import unittest

from backend.comment import Comment
from backend.favorite import Favorites
from backend.rating import Rating
from backend.review import Review
from backend.review_draft import ReviewDrafts


class TestReviewSocialPermissions(unittest.TestCase):

    def setUp(self):
        self.owner_id = 1
        self.other_user_id = 2
        self.media_id = 101
        self.review_id = 5001

        self.rating = Rating(
            self.owner_id,
            self.media_id
        )
        self.rating.set_rating(4.5)

        self.review = Review(
            user_id=self.owner_id,
            media_id=self.media_id,
            rating=self.rating.value,
            text="Original review."
        )

        self.comment = Comment(
            user_id=self.owner_id,
            review_id=self.review_id,
            text="Original comment."
        )

        self.favorites = Favorites(
            self.owner_id
        )
        self.favorites.add_favorite(
            self.media_id
        )

        self.drafts = ReviewDrafts()
        self.drafts.save_draft(
            user_id=self.owner_id,
            media_id=self.media_id,
            text="Unfinished review draft"
        )

    def test_non_owner_review_edit_does_not_mutate_connected_state(self):
        with self.assertRaises(PermissionError):
            self.review.edit_review(
                user_id=self.other_user_id,
                new_text="Unauthorized review edit"
            )

        self.assertEqual(
            self.review.text,
            "Original review."
        )
        self.assertEqual(
            self.rating.value,
            4.5
        )
        self.assertEqual(
            self.comment.text,
            "Original comment."
        )
        self.assertTrue(
            self.favorites.is_favorited(
                self.media_id
            )
        )
        self.assertEqual(
            self.drafts.get_draft(
                self.owner_id,
                self.media_id
            ),
            "Unfinished review draft"
        )

    def test_non_owner_review_delete_does_not_mutate_connected_state(self):
        with self.assertRaises(PermissionError):
            self.review.delete_review(
                user_id=self.other_user_id
            )

        self.assertEqual(
            self.review.text,
            "Original review."
        )
        self.assertEqual(
            self.comment.text,
            "Original comment."
        )
        self.assertTrue(
            self.favorites.is_favorited(
                self.media_id
            )
        )
        self.assertEqual(
            self.drafts.get_draft(
                self.owner_id,
                self.media_id
            ),
            "Unfinished review draft"
        )

    def test_non_owner_comment_edit_does_not_mutate_connected_state(self):
        with self.assertRaises(PermissionError):
            self.comment.edit_comment(
                user_id=self.other_user_id,
                new_text="Unauthorized comment edit"
            )

        self.assertEqual(
            self.comment.text,
            "Original comment."
        )
        self.assertEqual(
            self.review.text,
            "Original review."
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
        self.assertEqual(
            self.drafts.get_draft(
                self.owner_id,
                self.media_id
            ),
            "Unfinished review draft"
        )

    def test_non_owner_comment_delete_does_not_mutate_connected_state(self):
        with self.assertRaises(PermissionError):
            self.comment.delete_comment(
                user_id=self.other_user_id
            )

        self.assertEqual(
            self.comment.text,
            "Original comment."
        )
        self.assertEqual(
            self.review.text,
            "Original review."
        )
        self.assertTrue(
            self.favorites.is_favorited(
                self.media_id
            )
        )
        self.assertTrue(
            self.drafts.has_draft(
                self.owner_id,
                self.media_id
            )
        )


class TestReviewSocialMultiUserComments(unittest.TestCase):

    def test_multiple_users_can_comment_on_same_review_with_separate_ownership(self):
        review_id = 5001

        owner_comment = Comment(
            user_id=1,
            review_id=review_id,
            text="Review author's comment"
        )

        other_user_comment = Comment(
            user_id=2,
            review_id=review_id,
            text="Another user's comment"
        )

        other_user_comment.edit_comment(
            user_id=2,
            new_text="Updated by its owner"
        )

        with self.assertRaises(PermissionError):
            owner_comment.edit_comment(
                user_id=2,
                new_text="Unauthorized edit"
            )

        self.assertEqual(
            owner_comment.review_id,
            review_id
        )

        self.assertEqual(
            other_user_comment.review_id,
            review_id
        )

        self.assertEqual(
            owner_comment.text,
            "Review author's comment"
        )

        self.assertEqual(
            other_user_comment.text,
            "Updated by its owner"
        )


class TestReviewSocialFeatureInteractions(unittest.TestCase):

    def setUp(self):
        self.user_id = 1
        self.media_id = 101
        self.review_id = 5001

        self.rating = Rating(
            self.user_id,
            self.media_id
        )
        self.rating.set_rating(4.0)

        self.review = Review(
            user_id=self.user_id,
            media_id=self.media_id,
            rating=self.rating.value,
            text="Good movie."
        )

        self.comment = Comment(
            user_id=self.user_id,
            review_id=self.review_id,
            text="Initial comment"
        )

        self.favorites = Favorites(
            self.user_id
        )
        self.favorites.add_favorite(
            self.media_id
        )

        self.drafts = ReviewDrafts()
        self.drafts.save_draft(
            user_id=self.user_id,
            media_id=self.media_id,
            text="Separate unfinished draft"
        )

    def test_editing_comment_does_not_change_other_feature_state(self):
        self.comment.edit_comment(
            user_id=self.user_id,
            new_text="Updated comment"
        )

        self.assertEqual(
            self.comment.text,
            "Updated comment"
        )

        self.assertEqual(
            self.review.text,
            "Good movie."
        )

        self.assertEqual(
            self.rating.value,
            4.0
        )

        self.assertTrue(
            self.favorites.is_favorited(
                self.media_id
            )
        )

        self.assertEqual(
            self.drafts.get_draft(
                self.user_id,
                self.media_id
            ),
            "Separate unfinished draft"
        )

    def test_deleting_comment_does_not_change_other_feature_state(self):
        self.comment.delete_comment(
            user_id=self.user_id
        )

        self.assertIsNone(
            self.comment.text
        )

        self.assertEqual(
            self.review.text,
            "Good movie."
        )

        self.assertEqual(
            self.rating.value,
            4.0
        )

        self.assertTrue(
            self.favorites.is_favorited(
                self.media_id
            )
        )

        self.assertTrue(
            self.drafts.has_draft(
                self.user_id,
                self.media_id
            )
        )

    def test_removing_favorite_does_not_change_review_comment_rating_or_draft(self):
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
            self.review.text,
            "Good movie."
        )

        self.assertEqual(
            self.comment.text,
            "Initial comment"
        )

        self.assertEqual(
            self.drafts.get_draft(
                self.user_id,
                self.media_id
            ),
            "Separate unfinished draft"
        )

    def test_successful_submission_clears_only_matching_draft(self):
        self.drafts.save_draft(
            user_id=2,
            media_id=self.media_id,
            text="Other user's draft"
        )

        self.drafts.save_draft(
            user_id=self.user_id,
            media_id=202,
            text="Other media draft"
        )

        draft_text = self.drafts.get_draft(
            self.user_id,
            self.media_id
        )

        submitted_review = Review(
            user_id=self.user_id,
            media_id=self.media_id,
            rating=self.rating.value,
            text=draft_text
        )

        self.drafts.clear_draft(
            self.user_id,
            self.media_id
        )

        self.assertEqual(
            submitted_review.text,
            "Separate unfinished draft"
        )

        self.assertFalse(
            self.drafts.has_draft(
                self.user_id,
                self.media_id
            )
        )

        self.assertEqual(
            self.drafts.get_draft(
                2,
                self.media_id
            ),
            "Other user's draft"
        )

        self.assertEqual(
            self.drafts.get_draft(
                self.user_id,
                202
            ),
            "Other media draft"
        )

    def test_failed_submission_keeps_draft_and_other_feature_state(self):
        invalid_text = "x" * 5001

        self.drafts.save_draft(
            user_id=self.user_id,
            media_id=self.media_id,
            text=invalid_text
        )

        with self.assertRaises(ValueError):
            Review(
                user_id=self.user_id,
                media_id=self.media_id,
                rating=self.rating.value,
                text=invalid_text
            )

        self.assertEqual(
            self.drafts.get_draft(
                self.user_id,
                self.media_id
            ),
            invalid_text
        )

        self.assertEqual(
            self.review.text,
            "Good movie."
        )

        self.assertEqual(
            self.comment.text,
            "Initial comment"
        )

        self.assertTrue(
            self.favorites.is_favorited(
                self.media_id
            )
        )


if __name__ == "__main__":
    unittest.main()
