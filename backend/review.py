class Review:
    MAX_LENGTH = 5000

    def __init__(self, user_id, media_id, rating, text):
        self.user_id = user_id
        self.media_id = media_id
        self.rating = rating
        self.text = None
        self.set_text(text)

    def set_text(self, text):
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

    def verify_owner(self, user_id):
        if user_id != self.user_id:
            raise PermissionError(
                "Only the owner of this review can modify it."
            )

    def edit_review(self, user_id, new_text):
        self.verify_owner(user_id)
        self.set_text(new_text)

    def delete_review(self, user_id):
        self.verify_owner(user_id)
        self.text = None

    def to_dict(self):
        if self.text is None:
            return None

        return {
            "user_id": self.user_id,
            "media_id": self.media_id,
            "rating": self.rating,
            "text": self.text
        }