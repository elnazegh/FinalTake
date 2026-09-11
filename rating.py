class Rating:
    MIN_RATING = 0.5
    MAX_RATING = 5.0

    def __init__(self, user_id, media_id):
        self.user_id = user_id
        self.media_id = media_id
        self.value = None

    def set_rating(self, value):
        """Create or update a rating."""

        if not self.is_valid_rating(value):
            raise ValueError(
                "Rating must be between 0.5 and 5.0 "
                "in half-star increments."
            )

        self.value = float(value)

    def delete_rating(self):
        """Delete the current rating."""
        self.value = None

    @staticmethod
    def is_valid_rating(value):
        if not isinstance(value, (int, float)):
            return False

        if value < 0.5 or value > 5.0:
            return False

        # Valid ratings multiplied by 2 should be whole numbers.
        # Examples:
        # 3.5 * 2 = 7
        # 4.0 * 2 = 8
        # 3.7 * 2 = 7.4 (invalid)
        return (value * 2).is_integer()
