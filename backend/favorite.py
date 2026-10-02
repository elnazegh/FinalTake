class Favorites:
    def __init__(self, user_id):
        self.user_id = user_id
        self.media_ids = set()

    def add_favorite(self, media_id):
        """Add a media item to the user's favorites."""
        if media_id in self.media_ids:
            return False

        self.media_ids.add(media_id)
        return True

    def remove_favorite(self, media_id):
        """Remove a media item from the user's favorites."""
        if media_id not in self.media_ids:
            return False

        self.media_ids.remove(media_id)
        return True

    def is_favorited(self, media_id):
        """Check whether a media item is already favorited."""
        return media_id in self.media_ids

    def get_favorites(self):
        """Return the user's current favorites."""
        return list(self.media_ids)