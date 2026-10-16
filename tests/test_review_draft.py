import unittest

from backend.review import Review
from backend.review_draft import ReviewDrafts


class TestReviewDraftSaveAndRecovery(unittest.TestCase):

    def setUp(self):
        self.drafts = ReviewDrafts()

    def test_save_review_draft(self):
        self.drafts.save_draft(
            user_id=1,
            media_id=101,
            text="Unfinished review"
        )

        self.assertTrue(
            self.drafts.has_draft(
                user_id=1,
                media_id=101
            )
        )

    def test_recover_saved_review_draft(self):
        self.drafts.save_draft(
            user_id=1,
            media_id=101,
            text="Recovered review text"
        )

        draft = self.drafts.get_draft(
            user_id=1,
            media_id=101
        )

        self.assertEqual(
            draft,
            "Recovered review text"
        )

    def test_new_save_overwrites_existing_draft(self):
        self.drafts.save_draft(
            user_id=1,
            media_id=101,
            text="First version"
        )

        self.drafts.save_draft(
            user_id=1,
            media_id=101,
            text="Updated version"
        )

        draft = self.drafts.get_draft(
            user_id=1,
            media_id=101
        )

        self.assertEqual(
            draft,
            "Updated version"
        )

    def test_empty_draft_can_be_saved(self):
        self.drafts.save_draft(
            user_id=1,
            media_id=101,
            text=""
        )

        self.assertTrue(
            self.drafts.has_draft(
                user_id=1,
                media_id=101
            )
        )

        self.assertEqual(
            self.drafts.get_draft(
                user_id=1,
                media_id=101
            ),
            ""
        )

    def test_missing_draft_returns_none(self):
        draft = self.drafts.get_draft(
            user_id=1,
            media_id=101
        )

        self.assertIsNone(draft)


class TestReviewDraftIsolation(unittest.TestCase):

    def setUp(self):
        self.drafts = ReviewDrafts()

    def test_drafts_are_separate_between_users(self):
        self.drafts.save_draft(
            user_id=1,
            media_id=101,
            text="User 1 draft"
        )

        self.drafts.save_draft(
            user_id=2,
            media_id=101,
            text="User 2 draft"
        )

        self.assertEqual(
            self.drafts.get_draft(
                user_id=1,
                media_id=101
            ),
            "User 1 draft"
        )

        self.assertEqual(
            self.drafts.get_draft(
                user_id=2,
                media_id=101
            ),
            "User 2 draft"
        )

    def test_drafts_are_separate_between_media(self):
        self.drafts.save_draft(
            user_id=1,
            media_id=101,
            text="Media 101 draft"
        )

        self.drafts.save_draft(
            user_id=1,
            media_id=202,
            text="Media 202 draft"
        )

        self.assertEqual(
            self.drafts.get_draft(
                user_id=1,
                media_id=101
            ),
            "Media 101 draft"
        )

        self.assertEqual(
            self.drafts.get_draft(
                user_id=1,
                media_id=202
            ),
            "Media 202 draft"
        )


class TestReviewDraftValidation(unittest.TestCase):

    def setUp(self):
        self.drafts = ReviewDrafts()

    def test_draft_requires_user(self):
        with self.assertRaises(ValueError):
            self.drafts.save_draft(
                user_id=None,
                media_id=101,
                text="Draft"
            )

    def test_draft_requires_media(self):
        with self.assertRaises(ValueError):
            self.drafts.save_draft(
                user_id=1,
                media_id=None,
                text="Draft"
            )

    def test_draft_must_be_text(self):
        with self.assertRaises(ValueError):
            self.drafts.save_draft(
                user_id=1,
                media_id=101,
                text=123
            )

    def test_get_draft_requires_valid_user(self):
        with self.assertRaises(ValueError):
            self.drafts.get_draft(
                user_id=None,
                media_id=101
            )

    def test_get_draft_requires_valid_media(self):
        with self.assertRaises(ValueError):
            self.drafts.get_draft(
                user_id=1,
                media_id=None
            )


class TestReviewDraftClear(unittest.TestCase):

    def setUp(self):
        self.drafts = ReviewDrafts()

    def test_clear_existing_draft(self):
        self.drafts.save_draft(
            user_id=1,
            media_id=101,
            text="Draft to clear"
        )

        result = self.drafts.clear_draft(
            user_id=1,
            media_id=101
        )

        self.assertTrue(result)

        self.assertFalse(
            self.drafts.has_draft(
                user_id=1,
                media_id=101
            )
        )

    def test_clear_missing_draft_returns_false(self):
        result = self.drafts.clear_draft(
            user_id=1,
            media_id=101
        )

        self.assertFalse(result)

    def test_clearing_one_draft_does_not_clear_others(self):
        self.drafts.save_draft(
            user_id=1,
            media_id=101,
            text="First draft"
        )

        self.drafts.save_draft(
            user_id=2,
            media_id=101,
            text="Second draft"
        )

        self.drafts.clear_draft(
            user_id=1,
            media_id=101
        )

        self.assertIsNone(
            self.drafts.get_draft(
                user_id=1,
                media_id=101
            )
        )

        self.assertEqual(
            self.drafts.get_draft(
                user_id=2,
                media_id=101
            ),
            "Second draft"
        )


class TestReviewDraftSubmissionLifecycle(unittest.TestCase):

    def setUp(self):
        self.drafts = ReviewDrafts()

    def test_successful_review_submission_clears_draft(self):
        self.drafts.save_draft(
            user_id=1,
            media_id=101,
            text="Finished review"
        )

        draft_text = self.drafts.get_draft(
            user_id=1,
            media_id=101
        )

        review = Review(
            user_id=1,
            media_id=101,
            rating=4.5,
            text=draft_text
        )

        self.drafts.clear_draft(
            user_id=1,
            media_id=101
        )

        self.assertEqual(
            review.text,
            "Finished review"
        )

        self.assertFalse(
            self.drafts.has_draft(
                user_id=1,
                media_id=101
            )
        )

    def test_failed_review_submission_keeps_draft(self):
        invalid_text = "x" * 5001

        self.drafts.save_draft(
            user_id=1,
            media_id=101,
            text=invalid_text
        )

        with self.assertRaises(ValueError):
            Review(
                user_id=1,
                media_id=101,
                rating=4.5,
                text=invalid_text
            )

        self.assertTrue(
            self.drafts.has_draft(
                user_id=1,
                media_id=101
            )
        )

        self.assertEqual(
            self.drafts.get_draft(
                user_id=1,
                media_id=101
            ),
            invalid_text
        )


if __name__ == "__main__":
    unittest.main()
