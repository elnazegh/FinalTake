class Comment:
    def __init__(self, user_id, review_id, text):
        if user_id is None:
            raise ValueError("Comment must have a user.")

        if review_id is None:
            raise ValueError("Comment must belong to a review.")

        self.user_id = user_id
        self.review_id = review_id
        self.text = None

        self.set_text(text)

    def set_text(self, text):
        """Set and validate the comment text."""

        if not isinstance(text, str):
            raise ValueError("Comment must be text.")

        text = text.strip()

        if not text:
            raise ValueError("Comment cannot be empty.")

        self.text = text

    def verify_owner(self, user_id):
        """Verify that the supplied user owns this comment."""

        if user_id != self.user_id:
            raise PermissionError(
                "Only the owner of this comment can modify it."
            )

    def edit_comment(self, user_id, new_text):
        """Edit a comment if the user owns it."""

        self.verify_owner(user_id)

        if self.text is None:
            raise ValueError("Cannot edit a deleted comment.")

        self.set_text(new_text)

    def delete_comment(self, user_id):
        """Delete a comment if the user owns it."""

        self.verify_owner(user_id)

        if self.text is None:
            raise ValueError(
                "Comment has already been deleted."
            )

        self.text = None

    def to_dict(self):
        """Return comment data for display or later API use."""

        if self.text is None:
            return None

        return {
            "user_id": self.user_id,
            "review_id": self.review_id,
            "text": self.text
        }
