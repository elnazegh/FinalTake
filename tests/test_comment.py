import unittest

from backend.comment import Comment


class TestCommentCreationAndValidation(unittest.TestCase):

    def test_create_comment(self):
        comment = Comment(
            user_id=1,
            review_id=10,
            text="I agree with this review."
        )

        self.assertEqual(comment.user_id, 1)
        self.assertEqual(comment.review_id, 10)
        self.assertEqual(
            comment.text,
            "I agree with this review."
        )

    def test_comment_text_is_trimmed(self):
        comment = Comment(
            user_id=1,
            review_id=10,
            text="  Good point.  "
        )

        self.assertEqual(
            comment.text,
            "Good point."
        )

    def test_comment_requires_user(self):
        with self.assertRaises(ValueError):
            Comment(
                user_id=None,
                review_id=10,
                text="Comment"
            )

    def test_comment_requires_review(self):
        with self.assertRaises(ValueError):
            Comment(
                user_id=1,
                review_id=None,
                text="Comment"
            )

    def test_comment_cannot_be_empty(self):
        with self.assertRaises(ValueError):
            Comment(
                user_id=1,
                review_id=10,
                text=""
            )

    def test_comment_cannot_be_whitespace_only(self):
        with self.assertRaises(ValueError):
            Comment(
                user_id=1,
                review_id=10,
                text="   "
            )

    def test_comment_must_be_text(self):
        with self.assertRaises(ValueError):
            Comment(
                user_id=1,
                review_id=10,
                text=123
            )


class TestCommentDisplay(unittest.TestCase):

    def test_comment_to_dict(self):
        comment = Comment(
            user_id=1,
            review_id=10,
            text="Good review."
        )

        comment_data = comment.to_dict()

        self.assertEqual(
            comment_data["user_id"],
            1
        )

        self.assertEqual(
            comment_data["review_id"],
            10
        )

        self.assertEqual(
            comment_data["text"],
            "Good review."
        )

    def test_deleted_comment_has_no_display_data(self):
        comment = Comment(
            user_id=1,
            review_id=10,
            text="Comment to delete"
        )

        comment.delete_comment(
            user_id=1
        )

        self.assertIsNone(
            comment.to_dict()
        )


class TestCommentEditingAndDeletion(unittest.TestCase):

    def test_owner_can_edit_comment(self):
        comment = Comment(
            user_id=1,
            review_id=10,
            text="Original comment"
        )

        comment.edit_comment(
            user_id=1,
            new_text="Updated comment"
        )

        self.assertEqual(
            comment.text,
            "Updated comment"
        )

    def test_edit_preserves_user_and_review_associations(self):
        comment = Comment(
            user_id=1,
            review_id=10,
            text="Original comment"
        )

        comment.edit_comment(
            user_id=1,
            new_text="Updated comment"
        )

        self.assertEqual(
            comment.user_id,
            1
        )

        self.assertEqual(
            comment.review_id,
            10
        )

    def test_empty_edit_is_rejected_without_changing_comment(self):
        comment = Comment(
            user_id=1,
            review_id=10,
            text="Original comment"
        )

        with self.assertRaises(ValueError):
            comment.edit_comment(
                user_id=1,
                new_text=""
            )

        self.assertEqual(
            comment.text,
            "Original comment"
        )

    def test_owner_can_delete_comment(self):
        comment = Comment(
            user_id=1,
            review_id=10,
            text="Comment to delete"
        )

        comment.delete_comment(
            user_id=1
        )

        self.assertIsNone(
            comment.text
        )

    def test_deleted_comment_cannot_be_edited(self):
        comment = Comment(
            user_id=1,
            review_id=10,
            text="Comment to delete"
        )

        comment.delete_comment(
            user_id=1
        )

        with self.assertRaises(ValueError):
            comment.edit_comment(
                user_id=1,
                new_text="Restored comment"
            )

        self.assertIsNone(
            comment.text
        )

    def test_deleted_comment_cannot_be_deleted_again(self):
        comment = Comment(
            user_id=1,
            review_id=10,
            text="Comment to delete"
        )

        comment.delete_comment(
            user_id=1
        )

        with self.assertRaises(ValueError):
            comment.delete_comment(
                user_id=1
            )

        self.assertIsNone(
            comment.text
        )


class TestCommentOwnership(unittest.TestCase):

    def test_non_owner_cannot_edit_comment(self):
        comment = Comment(
            user_id=1,
            review_id=10,
            text="Original comment"
        )

        with self.assertRaises(PermissionError):
            comment.edit_comment(
                user_id=2,
                new_text="Unauthorized edit"
            )

        self.assertEqual(
            comment.text,
            "Original comment"
        )

    def test_non_owner_cannot_delete_comment(self):
        comment = Comment(
            user_id=1,
            review_id=10,
            text="Original comment"
        )

        with self.assertRaises(PermissionError):
            comment.delete_comment(
                user_id=2
            )

        self.assertEqual(
            comment.text,
            "Original comment"
        )


if __name__ == "__main__":
    unittest.main()
