
import unittest

from backend.comment import Comment
from backend.favorite import Favorites
from backend.rating import Rating
from backend.review import Review
from backend.review_draft import ReviewDrafts


class TestCC41SecurityEvaluation(unittest.TestCase):
    """Independent CC4.1 regression checks for Reviews/Social."""

    def test_multi_user_multi_media_draft_isolation(self):
        drafts = ReviewDrafts()
        expected = {}

        # Create drafts across three users and three media items.
        for user_id in (1, 2, 3):
            for media_id in (101, 202, 303):
                text = f"User {user_id}, media {media_id} draft"
                drafts.save_draft(user_id, media_id, text)
                expected[(user_id, media_id)] = text

        # Overwrite one draft without changing the other eight.
        drafts.save_draft(2, 202, "Updated user 2 draft")
        expected[(2, 202)] = "Updated user 2 draft"

        # Clear another user's draft for a different media item.
        self.assertTrue(drafts.clear_draft(1, 101))
        del expected[(1, 101)]

        # Repeating the clear must not affect any other draft.
        self.assertFalse(drafts.clear_draft(1, 101))

        # Verify every remaining user/media combination.
        for (user_id, media_id), text in expected.items():
            with self.subTest(user_id=user_id, media_id=media_id):
                self.assertTrue(drafts.has_draft(user_id, media_id))
                self.assertEqual(
                    drafts.get_draft(user_id, media_id),
                    text,
                )

        self.assertFalse(drafts.has_draft(1, 101))
        self.assertIsNone(drafts.get_draft(1, 101))
        self.assertEqual(len(drafts.drafts), len(expected))

    def test_invalid_draft_operations_preserve_existing_data(self):
        drafts = ReviewDrafts()

        original_drafts = {
            (1, 101): "User 1 first draft",
            (1, 202): "User 1 second draft",
            (2, 101): "User 2 first draft",
            (3, 303): "User 3 draft",
        }

        for (user_id, media_id), text in original_drafts.items():
            drafts.save_draft(user_id, media_id, text)

        snapshot = dict(drafts.drafts)

        # Invalid saves must not overwrite existing entries.
        invalid_saves = (
            (None, 101, "Missing user"),
            (1, None, "Missing media"),
            (1, 101, 123),
            (2, 101, None),
        )

        for user_id, media_id, text in invalid_saves:
            with self.subTest(
                operation="save",
                user_id=user_id,
                media_id=media_id,
            ):
                with self.assertRaises(ValueError):
                    drafts.save_draft(user_id, media_id, text)

                self.assertEqual(drafts.drafts, snapshot)

        # Invalid lookups and clears must also preserve data.
        for operation in (
            drafts.get_draft,
            drafts.has_draft,
            drafts.clear_draft,
        ):
            for user_id, media_id in (
                (None, 101),
                (1, None),
            ):
                with self.subTest(
                    operation=operation.__name__,
                    user_id=user_id,
                    media_id=media_id,
                ):
                    with self.assertRaises(ValueError):
                        operation(user_id, media_id)

                    self.assertEqual(drafts.drafts, snapshot)

        # A legitimate operation must still work afterward.
        drafts.save_draft(1, 101, "Recovered draft")

        self.assertEqual(
            drafts.get_draft(1, 101),
            "Recovered draft",
        )

        for key, text in original_drafts.items():
            if key != (1, 101):
                self.assertEqual(drafts.get_draft(*key), text)

    def test_cross_feature_recovery_after_rejected_operations(self):
        owner_id = 1
        other_user_id = 2
        media_id = 101

        owner_rating = Rating(owner_id, media_id)
        owner_rating.set_rating(4.5)

        other_rating = Rating(other_user_id, media_id)
        other_rating.set_rating(3.5)

        owner_review = Review(
            user_id=owner_id,
            media_id=media_id,
            rating=owner_rating.value,
            text="Original owner review",
        )

        other_review = Review(
            user_id=other_user_id,
            media_id=media_id,
            rating=other_rating.value,
            text="Original other user review",
        )

        owner_comment = Comment(
            user_id=owner_id,
            review_id=1001,
            text="Original owner comment",
        )

        other_comment = Comment(
            user_id=other_user_id,
            review_id=1002,
            text="Original other user comment",
        )

        owner_favorites = Favorites(owner_id)
        owner_favorites.add_favorite(media_id)

        other_favorites = Favorites(other_user_id)
        other_favorites.add_favorite(media_id)

        drafts = ReviewDrafts()
        drafts.save_draft(owner_id, media_id, "Owner draft")
        drafts.save_draft(other_user_id, media_id, "Other user draft")

        # Reject invalid operations in three different features.
        with self.assertRaises(ValueError):
            owner_review.edit_review(owner_id, "   ")

        with self.assertRaises(ValueError):
            owner_comment.edit_comment(owner_id, 123)

        with self.assertRaises(ValueError):
            drafts.save_draft(other_user_id, media_id, None)

        # Rejected operations must preserve all existing data.
        self.assertEqual(owner_review.text, "Original owner review")
        self.assertEqual(other_review.text, "Original other user review")

        self.assertEqual(owner_comment.text, "Original owner comment")
        self.assertEqual(other_comment.text, "Original other user comment")

        self.assertEqual(drafts.get_draft(owner_id, media_id), "Owner draft")
        self.assertEqual(
            drafts.get_draft(other_user_id, media_id),
            "Other user draft",
        )

        self.assertEqual(owner_rating.value, 4.5)
        self.assertEqual(other_rating.value, 3.5)

        self.assertTrue(owner_favorites.is_favorited(media_id))
        self.assertTrue(other_favorites.is_favorited(media_id))

        # Legitimate operations must still succeed after rejection.
        owner_review.edit_review(owner_id, "Recovered owner review")
        owner_comment.edit_comment(owner_id, "Recovered owner comment")
        drafts.save_draft(owner_id, media_id, "Recovered owner draft")

        self.assertEqual(owner_review.text, "Recovered owner review")
        self.assertEqual(owner_comment.text, "Recovered owner comment")
        self.assertEqual(
            drafts.get_draft(owner_id, media_id),
            "Recovered owner draft",
        )

        # The other user's data must remain unchanged.
        self.assertEqual(other_review.text, "Original other user review")
        self.assertEqual(other_comment.text, "Original other user comment")
        self.assertEqual(
            drafts.get_draft(other_user_id, media_id),
            "Other user draft",
        )

        self.assertEqual(owner_rating.value, 4.5)
        self.assertEqual(other_rating.value, 3.5)
        self.assertTrue(owner_favorites.is_favorited(media_id))
        self.assertTrue(other_favorites.is_favorited(media_id))


if __name__ == "__main__":
    unittest.main()
