
"""Review data and owner-checked review operations."""

try:
    from .tag import normalize_tags
except ImportError:
    from tag import normalize_tags


class Review:
    MAX_LENGTH = 5000

    def __init__(self, user_id, media_id, rating, text, tags=None):
        self.user_id = user_id
        self.media_id = media_id
        self.rating = rating
        self._tags = tuple(normalize_tags(tags))
        self.text = None
        self.set_text(text)

    @property
    def tags(self):
        """Return a copy so tag changes must use edit_tags()."""
        return list(self._tags)

    def _validate_combined_length(self, text, tags):
        tag_text = ", ".join(tags)

        if len(text) + len(tag_text) > self.MAX_LENGTH:
            raise ValueError(
                f"Review text and tags cannot exceed "
                f"{self.MAX_LENGTH} characters."
            )

    def set_text(self, text):
        if not isinstance(text, str):
            raise ValueError("Review must be text.")

        text = text.strip()

        if not text:
            raise ValueError("Review cannot be empty.")

        self._validate_combined_length(text, self._tags)
        self.text = text

    def verify_owner(self, user_id):
        if user_id != self.user_id:
            raise PermissionError(
                "Only the owner of this review can modify it."
            )

    def edit_review(self, user_id, new_text):
        self.verify_owner(user_id)

        if self.text is None:
            raise ValueError("Cannot edit a deleted review.")

        self.set_text(new_text)

    def edit_tags(self, user_id, new_tags):
        """Replace tags after validating ownership and combined length."""
        self.verify_owner(user_id)

        if self.text is None:
            raise ValueError("Cannot edit tags on a deleted review.")

        normalized = normalize_tags(new_tags)
        self._validate_combined_length(self.text, normalized)

        self._tags = tuple(normalized)

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
            "text": self.text,
            "tags": self.tags
        }
