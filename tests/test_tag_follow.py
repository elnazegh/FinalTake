
"""FC4G6-76: Tag following, unfollowing, and per-user API isolation."""

import unittest

from backend.tag_follow import TagFollows, normalize_follow_tag
from backend.tag_follow_api import tag_follows
from backend import app as app_module


class TagFollowModelTests(unittest.TestCase):

    def setUp(self):
        self.follows = TagFollows()

    def test_normalizes_single_tag(self):
        self.assertEqual(
            normalize_follow_tag("  SCI   FI "),
            "sci fi"
        )

    def test_rejects_empty_and_multiple_tags(self):
        for value in (
            None,
            "",
            "   ",
            "drama,comedy",
            ["drama"]
        ):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    normalize_follow_tag(value)

    def test_following_same_tag_twice_is_idempotent(self):
        self.assertTrue(
            self.follows.follow(1, "Drama")
        )

        self.assertFalse(
            self.follows.follow(1, "DRAMA")
        )

        self.assertEqual(
            self.follows.get_followed_tags(1),
            ["drama"]
        )

    def test_unfollow_removes_only_selected_tag(self):
        self.follows.follow(1, "Drama")
        self.follows.follow(1, "Comedy")

        self.assertTrue(
            self.follows.unfollow(1, "DRAMA")
        )

        self.assertEqual(
            self.follows.get_followed_tags(1),
            ["comedy"]
        )

    def test_unfollow_missing_tag_is_safe(self):
        self.assertFalse(
            self.follows.unfollow(1, "Drama")
        )

        self.assertEqual(
            self.follows.get_followed_tags(1),
            []
        )

    def test_follow_state_is_isolated_by_user(self):
        self.follows.follow(1, "Drama")
        self.follows.follow(2, "Comedy")

        self.assertFalse(
            self.follows.is_following(2, "Drama")
        )

        self.assertTrue(
            self.follows.is_following(1, "Drama")
        )

        self.follows.unfollow(2, "Comedy")

        self.assertEqual(
            self.follows.get_followed_tags(1),
            ["drama"]
        )

    def test_returned_tags_cannot_modify_follow_state(self):
        self.follows.follow(1, "Drama")

        tags = self.follows.get_followed_tags(1)
        tags.append("injected")

        self.assertEqual(
            self.follows.get_followed_tags(1),
            ["drama"]
        )

    def test_user_is_required(self):
        with self.assertRaises(ValueError):
            self.follows.follow(None, "Drama")


class TagFollowApiTests(unittest.TestCase):

    def setUp(self):
        self.old_secret_key = (
            app_module.app.config.get("SECRET_KEY")
        )

        app_module.app.config.update(
            TESTING=True,
            SECRET_KEY="tag-follow-tests-only"
        )

        tag_follows.clear()
        self.client = app_module.app.test_client()
        self.login_as(1)

    def tearDown(self):
        tag_follows.clear()
        app_module.app.config["SECRET_KEY"] = (
            self.old_secret_key
        )

    def login_as(self, user_id):
        with self.client.session_transaction() as session_data:
            session_data["user_id"] = user_id

    def test_authenticated_user_can_follow_tag(self):
        response = self.client.post(
            "/api/tags/following",
            json={"tag": " SCI  FI "}
        )

        self.assertEqual(
            response.status_code,
            201
        )

        self.assertTrue(
            response.get_json()["created"]
        )

        self.assertEqual(
            response.get_json()["tags"],
            ["sci fi"]
        )

    def test_duplicate_follow_does_not_create_duplicate(self):
        self.client.post(
            "/api/tags/following",
            json={"tag": "Drama"}
        )

        response = self.client.post(
            "/api/tags/following",
            json={"tag": "DRAMA"}
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertFalse(
            response.get_json()["created"]
        )

        self.assertEqual(
            response.get_json()["tags"],
            ["drama"]
        )

    def test_get_returns_only_current_users_tags(self):
        self.client.post(
            "/api/tags/following",
            json={"tag": "Drama"}
        )

        self.login_as(2)

        self.client.post(
            "/api/tags/following",
            json={"tag": "Comedy"}
        )

        response = self.client.get(
            "/api/tags/following"
        )

        self.assertEqual(
            response.get_json()["tags"],
            ["comedy"]
        )

        self.login_as(1)

        response = self.client.get(
            "/api/tags/following"
        )

        self.assertEqual(
            response.get_json()["tags"],
            ["drama"]
        )

    def test_unfollow_only_affects_current_user(self):
        self.client.post(
            "/api/tags/following",
            json={"tag": "Drama"}
        )

        self.login_as(2)

        self.client.post(
            "/api/tags/following",
            json={"tag": "Drama"}
        )

        response = self.client.delete(
            "/api/tags/following/drama"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertTrue(
            response.get_json()["removed"]
        )

        self.login_as(1)

        self.assertEqual(
            self.client.get(
                "/api/tags/following"
            ).get_json()["tags"],
            ["drama"]
        )

    def test_unfollow_missing_tag_is_idempotent(self):
        response = self.client.delete(
            "/api/tags/following/drama"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertFalse(
            response.get_json()["removed"]
        )

    def test_anonymous_user_cannot_follow_or_list_or_unfollow(self):
        anonymous = app_module.app.test_client()

        self.assertEqual(
            anonymous.get(
                "/api/tags/following"
            ).status_code,
            401
        )

        self.assertEqual(
            anonymous.post(
                "/api/tags/following",
                json={"tag": "Drama"}
            ).status_code,
            401
        )

        self.assertEqual(
            anonymous.delete(
                "/api/tags/following/drama"
            ).status_code,
            401
        )

    def test_forged_user_id_does_not_change_owner(self):
        response = self.client.post(
            "/api/tags/following",
            json={
                "tag": "Drama",
                "user_id": 99
            }
        )

        self.assertEqual(
            response.status_code,
            201
        )

        self.assertEqual(
            tag_follows.get_followed_tags(99),
            []
        )

        self.assertEqual(
            tag_follows.get_followed_tags(1),
            ["drama"]
        )

    def test_invalid_tag_is_rejected_without_creating_state(self):
        for value in (
            "",
            "drama, comedy",
            12
        ):
            with self.subTest(value=value):
                response = self.client.post(
                    "/api/tags/following",
                    json={"tag": value}
                )

                self.assertEqual(
                    response.status_code,
                    400
                )

        self.assertEqual(
            tag_follows.get_followed_tags(1),
            []
        )

    def test_non_object_json_is_rejected(self):
        response = self.client.post(
            "/api/tags/following",
            json=["Drama"]
        )

        self.assertEqual(
            response.status_code,
            400
        )

    def test_following_does_not_modify_review_tags(self):
        from backend.review import Review

        review = Review(
            1,
            "1",
            4.5,
            "Great film",
            tags="Drama"
        )

        self.client.post(
            "/api/tags/following",
            json={"tag": "Comedy"}
        )

        self.assertEqual(
            review.tags,
            ["drama"]
        )

        self.assertEqual(
            tag_follows.get_followed_tags(1),
            ["comedy"]
        )


if __name__ == "__main__":
    unittest.main()
