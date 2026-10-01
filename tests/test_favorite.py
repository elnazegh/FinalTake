import unittest

from backend.favorite import Favorites


class TestFavorites(unittest.TestCase):

    def test_add_favorite(self):
        favorites = Favorites(user_id=1)

        result = favorites.add_favorite(101)

        self.assertTrue(result)
        self.assertTrue(
            favorites.is_favorited(101)
        )

    def test_duplicate_favorite_is_not_added(self):
        favorites = Favorites(user_id=1)

        favorites.add_favorite(101)
        result = favorites.add_favorite(101)

        self.assertFalse(result)
        self.assertEqual(
            len(favorites.get_favorites()),
            1
        )

    def test_remove_favorite(self):
        favorites = Favorites(user_id=1)

        favorites.add_favorite(101)
        result = favorites.remove_favorite(101)

        self.assertTrue(result)
        self.assertFalse(
            favorites.is_favorited(101)
        )

    def test_remove_nonexistent_favorite(self):
        favorites = Favorites(user_id=1)

        result = favorites.remove_favorite(101)

        self.assertFalse(result)

    def test_favorite_status_false_before_add(self):
        favorites = Favorites(user_id=1)

        self.assertFalse(
            favorites.is_favorited(101)
        )

    def test_favorite_has_correct_user(self):
        favorites = Favorites(user_id=1)

        self.assertEqual(
            favorites.user_id,
            1
        )

    def test_favorite_has_correct_media(self):
        favorites = Favorites(user_id=1)

        favorites.add_favorite(101)

        self.assertIn(
            101,
            favorites.get_favorites()
        )

    def test_favorites_are_separate_between_users(self):
        user_one_favorites = Favorites(user_id=1)
        user_two_favorites = Favorites(user_id=2)

        user_one_favorites.add_favorite(101)

        self.assertTrue(
            user_one_favorites.is_favorited(101)
        )

        self.assertFalse(
            user_two_favorites.is_favorited(101)
        )


if __name__ == "__main__":
    unittest.main()