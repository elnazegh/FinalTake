
"""In-memory following state for normalized review tags."""

try:
    from .tag import normalize_tags
except ImportError:
    from tag import normalize_tags


def normalize_follow_tag(tag):
    """Require exactly one nonempty normalized tag."""
    if not isinstance(tag, str):
        raise ValueError("Tag must be text.")

    if "," in tag:
        raise ValueError("Follow one tag at a time.")

    normalized = normalize_tags(tag)

    if len(normalized) != 1:
        raise ValueError("Tag cannot be empty.")

    return normalized[0]


class TagFollows:
    """Track a separate set of followed tags for each user."""

    def __init__(self):
        self._followed = {}

    @staticmethod
    def _check_user(user_id):
        if user_id is None:
            raise ValueError("A user is required.")

    def follow(self, user_id, tag):
        """Follow a tag; return True only if it was newly added."""
        self._check_user(user_id)
        normalized = normalize_follow_tag(tag)

        followed = self._followed.setdefault(user_id, set())

        if normalized in followed:
            return False

        followed.add(normalized)
        return True

    def unfollow(self, user_id, tag):
        """Unfollow a tag; return True if a follow was removed."""
        self._check_user(user_id)
        normalized = normalize_follow_tag(tag)

        followed = self._followed.get(user_id)

        if not followed or normalized not in followed:
            return False

        followed.remove(normalized)

        if not followed:
            del self._followed[user_id]

        return True

    def is_following(self, user_id, tag):
        self._check_user(user_id)
        normalized = normalize_follow_tag(tag)

        return normalized in self._followed.get(
            user_id, set()
        )

    def get_followed_tags(self, user_id):
        """Return a sorted copy rather than exposing internal state."""
        self._check_user(user_id)

        return sorted(
            self._followed.get(user_id, set())
        )

    def clear(self):
        """Reset temporary state between tests."""
        self._followed.clear()
