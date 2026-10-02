import unittest

from backend.rating import Rating


class TestRating(unittest.TestCase):

    def setUp(self):
        self.rating = Rating(
            user_id=1,
            media_id=101
        )

    def test_minimum_rating_is_valid(self):
        self.rating.set_rating(0.5)

        self.assertEqual(
            self.rating.value,
            0.5
        )

    def test_maximum_rating_is_valid(self):
        self.rating.set_rating(5.0)

        self.assertEqual(
            self.rating.value,
            5.0
        )

    def test_whole_star_rating_is_valid(self):
        self.rating.set_rating(4.0)

        self.assertEqual(
            self.rating.value,
            4.0
        )

    def test_half_star_rating_is_valid(self):
        self.rating.set_rating(3.5)

        self.assertEqual(
            self.rating.value,
            3.5
        )

    def test_rating_below_minimum_is_invalid(self):
        with self.assertRaises(ValueError):
            self.rating.set_rating(0.0)

    def test_rating_above_maximum_is_invalid(self):
        with self.assertRaises(ValueError):
            self.rating.set_rating(5.5)

    def test_non_half_star_increment_is_invalid(self):
        with self.assertRaises(ValueError):
            self.rating.set_rating(3.7)

    def test_rating_can_be_updated(self):
        self.rating.set_rating(4.0)
        self.rating.set_rating(2.5)

        self.assertEqual(
            self.rating.value,
            2.5
        )

    def test_rating_can_be_deleted(self):
        self.rating.set_rating(4.5)
        self.rating.delete_rating()

        self.assertIsNone(
            self.rating.value
        )

    def test_rating_has_correct_user(self):
        self.assertEqual(
            self.rating.user_id,
            1
        )

    def test_rating_has_correct_media(self):
        self.assertEqual(
            self.rating.media_id,
            101
        )


if __name__ == "__main__":
    unittest.main()