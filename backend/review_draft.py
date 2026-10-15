class ReviewDrafts:
    def __init__(self):
        self.drafts = {}

    @staticmethod
    def _validate_ids(user_id, media_id):
        if user_id is None:
            raise ValueError(
                "Review draft must have a user."
            )

        if media_id is None:
            raise ValueError(
                "Review draft must belong to media."
            )

    def save_draft(self, user_id, media_id, text):
        """Save or overwrite a review draft."""

        self._validate_ids(user_id, media_id)

        if not isinstance(text, str):
            raise ValueError(
                "Review draft must be text."
            )

        self.drafts[(user_id, media_id)] = text

    def get_draft(self, user_id, media_id):
        """Return a saved draft or None."""

        self._validate_ids(user_id, media_id)

        return self.drafts.get(
            (user_id, media_id)
        )

    def has_draft(self, user_id, media_id):
        """Check whether a saved draft exists."""

        self._validate_ids(user_id, media_id)

        return (
            user_id,
            media_id
        ) in self.drafts

    def clear_draft(self, user_id, media_id):
        """Remove a saved draft if it exists."""

        self._validate_ids(user_id, media_id)

        key = (
            user_id,
            media_id
        )

        if key not in self.drafts:
            return False

        del self.drafts[key]

        return True
