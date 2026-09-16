class Review:
    MAX_LENGTH = 5000

    def __init__(self, user_id, media_id, rating, text):
        self.user_id = user_id
        self.media_id = media_id
        self.rating = rating
        self.text = None

        self.set_text(text)

    def set_text(self, text):
        """Set the review text."""
        if not isinstance(text, str):
            raise ValueError("Review must be text.")

        text = text.strip()

        if not text:
            raise ValueError("Review cannot be empty.")

        if len(text) > self.MAX_LENGTH:
            raise ValueError(
                f"Review cannot exceed {self.MAX_LENGTH} characters."
            )

        self.text = text

    def __str__(self):
        return self.text
