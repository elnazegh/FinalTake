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

    def to_dict(self):
        """Return comment data for display or later API use."""

        return {
            "user_id": self.user_id,
            "review_id": self.review_id,
            "text": self.text
        }
