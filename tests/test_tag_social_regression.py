
"""FC4G6-295: Regression tests across Review Tags and Tag Following APIs."""

import unittest
from unittest.mock import patch

from backend import app as app_module
from backend.tag_follow_api import tag_follows


class TagSocialRegressionTests(unittest.TestCase):
    def setUp(self):
        self.media_lookup_patch = patch.object(
            app_module,
            "get_media_by_id",
            side_effect=lambda media_id: {
                "1": {"id": "1", "title": "The Dark Knight"},
                "2": {"id": "2", "title": "Dark"}
            }.get(str(media_id))
        )
        self.media_titles_patch = patch.object(
            app_module,
            "load_media_titles",
            side_effect=lambda media_ids: {
                str(media_id): title
                for media_id, title in (
                    ("1", "The Dark Knight"),
                    ("2", "Dark")
                )
                if str(media_id) in {str(value) for value in media_ids}
            }
        )
        self.media_lookup_patch.start()
        self.media_titles_patch.start()
        self.old_secret_key = app_module.app.config.get("SECRET_KEY")
        self.old_testing = app_module.app.config.get("TESTING")

        app_module.app.config.update(
            TESTING=True,
            SECRET_KEY="tag-social-regression-test-only"
        )

        app_module.reviews.clear()
        app_module.next_review_id = 1
        tag_follows.clear()

        self.client = app_module.app.test_client()
        self.login_as(1)

    def tearDown(self):
        app_module.reviews.clear()
        app_module.next_review_id = 1
        tag_follows.clear()

        app_module.app.config["SECRET_KEY"] = self.old_secret_key
        app_module.app.config["TESTING"] = self.old_testing
        self.media_titles_patch.stop()
        self.media_lookup_patch.stop()

    def login_as(self, user_id):
        with self.client.session_transaction() as current_session:
            current_session["user_id"] = user_id

    def create_review(self, tags=None, media_id="1", user_id=None):
        data = {
            "media_id": media_id,
            "rating": 4.5,
            "text": "A review for Tag regression testing."
        }

        if tags is not None:
            data["tags"] = tags

        if user_id is not None:
            data["user_id"] = user_id

        response = self.client.post("/api/reviews", json=data)
        self.assertEqual(response.status_code, 201)

        return response.get_json()["review"]

    def filtered_reviews(self, tag, media_id=None):
        query = {"tag": tag}

        if media_id is not None:
            query["media_id"] = media_id

        response = self.client.get(
            "/api/reviews",
            query_string=query
        )

        self.assertEqual(response.status_code, 200)
        return response.get_json()["reviews"]

    def test_create_filter_follow_and_unfollow_work_together(self):
        created = self.create_review(
            tags="Sci Fi, Drama, sci fi"
        )

        self.assertEqual(
            created["tags"],
            ["sci fi", "drama"]
        )

        matches = self.filtered_reviews(" SCI   FI ")

        self.assertEqual(
            [item["id"] for item in matches],
            [created["id"]]
        )

        follow = self.client.post(
            "/api/tags/following",
            json={"tag": "SCI FI"}
        )

        self.assertEqual(follow.status_code, 201)
        self.assertEqual(
            follow.get_json()["tags"],
            ["sci fi"]
        )

        unfollow = self.client.delete(
            "/api/tags/following/sci%20fi"
        )

        self.assertEqual(unfollow.status_code, 200)
        self.assertEqual(unfollow.get_json()["tags"], [])

        # Following is separate from whether matching reviews exist.
        self.assertEqual(
            len(self.filtered_reviews("sci fi")),
            1
        )

    def test_following_survives_deletion_of_a_tagged_review(self):
        review = self.create_review(tags="Drama")

        self.client.post(
            "/api/tags/following",
            json={"tag": "Drama"}
        )

        deleted = self.client.delete(
            f"/api/reviews/{review['id']}"
        )

        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(self.filtered_reviews("drama"), [])

        follows = self.client.get("/api/tags/following")

        self.assertEqual(
            follows.get_json()["tags"],
            ["drama"]
        )

    def test_tag_edit_updates_search_but_not_follow_state(self):
        review = self.create_review(tags="Drama")

        self.client.post(
            "/api/tags/following",
            json={"tag": "Drama"}
        )

        # FC4G6-73 did not introduce an HTTP edit-tags endpoint.
        app_module.reviews[review["id"]].edit_tags(
            1,
            "Action"
        )

        self.assertEqual(
            self.filtered_reviews("drama"),
            []
        )

        self.assertEqual(
            [
                item["id"]
                for item in self.filtered_reviews("ACTION")
            ],
            [review["id"]]
        )

        self.assertEqual(
            self.client.get(
                "/api/tags/following"
            ).get_json()["tags"],
            ["drama"]
        )

    def test_untagged_reviews_are_not_in_tag_filtered_results(self):
        untagged = self.create_review()
        tagged = self.create_review(tags="Comedy")

        self.assertEqual(untagged["tags"], [])

        self.assertEqual(
            [
                item["id"]
                for item in self.filtered_reviews("comedy")
            ],
            [tagged["id"]]
        )

        all_reviews = self.client.get("/api/reviews")

        self.assertEqual(
            len(all_reviews.get_json()["reviews"]),
            2
        )

    def test_session_identity_controls_review_and_follow_ownership(self):
        review = self.create_review(
            tags="Drama",
            user_id=999
        )

        self.assertEqual(review["user_id"], 1)

        followed = self.client.post(
            "/api/tags/following",
            json={
                "tag": "Drama",
                "user_id": 999
            }
        )

        self.assertEqual(followed.status_code, 201)

        self.assertEqual(
            tag_follows.get_followed_tags(999),
            []
        )

        self.assertEqual(
            tag_follows.get_followed_tags(1),
            ["drama"]
        )

    def test_different_users_can_follow_same_tag_without_cross_changes(self):
        self.client.post(
            "/api/tags/following",
            json={"tag": "Drama"}
        )

        self.login_as(2)

        self.client.post(
            "/api/tags/following",
            json={"tag": "Drama"}
        )

        self.client.delete(
            "/api/tags/following/drama"
        )

        self.assertEqual(
            self.client.get(
                "/api/tags/following"
            ).get_json()["tags"],
            []
        )

        self.login_as(1)

        self.assertEqual(
            self.client.get(
                "/api/tags/following"
            ).get_json()["tags"],
            ["drama"]
        )

    def test_nonowner_can_follow_tag_but_cannot_delete_review(self):
        review = self.create_review(tags="Drama")

        self.login_as(2)

        follow = self.client.post(
            "/api/tags/following",
            json={"tag": "Drama"}
        )

        self.assertEqual(follow.status_code, 201)

        attempted_delete = self.client.delete(
            f"/api/reviews/{review['id']}",
            json={"user_id": 1}
        )

        self.assertEqual(
            attempted_delete.status_code,
            403
        )

        self.assertEqual(
            len(self.filtered_reviews("drama")),
            1
        )

    def test_anonymous_user_cannot_mutate_but_can_browse_reviews(self):
        review = self.create_review(tags="Drama")
        anonymous = app_module.app.test_client()

        self.assertEqual(
            anonymous.post(
                "/api/tags/following",
                json={"tag": "Drama"}
            ).status_code,
            401
        )

        self.assertEqual(
            anonymous.post(
                "/api/reviews",
                json={
                    "media_id": "1",
                    "rating": 4.5,
                    "text": "Anonymous",
                    "tags": "Drama"
                }
            ).status_code,
            401
        )

        public_results = anonymous.get(
            "/api/reviews",
            query_string={"tag": "drama"}
        )

        self.assertEqual(
            public_results.status_code,
            200
        )

        self.assertEqual(
            [
                item["id"]
                for item in public_results.get_json()["reviews"]
            ],
            [review["id"]]
        )

    def test_invalid_tags_do_not_change_review_or_follow_state(self):
        bad_review = self.client.post(
            "/api/reviews",
            json={
                "media_id": "1",
                "rating": 4.5,
                "text": "Invalid tags",
                "tags": "Drama,,Comedy"
            }
        )

        self.assertEqual(bad_review.status_code, 400)

        bad_follow = self.client.post(
            "/api/tags/following",
            json={"tag": "Drama,Comedy"}
        )

        self.assertEqual(bad_follow.status_code, 400)
        self.assertEqual(app_module.reviews, {})

        self.assertEqual(
            tag_follows.get_followed_tags(1),
            []
        )

    def test_browsing_can_combine_media_and_tag_while_followed(self):
        first = self.create_review(
            tags="Drama",
            media_id="1"
        )

        self.create_review(
            tags="Drama",
            media_id="2"
        )

        self.client.post(
            "/api/tags/following",
            json={"tag": "Drama"}
        )

        results = self.filtered_reviews(
            "drama",
            media_id="1"
        )

        self.assertEqual(
            [item["id"] for item in results],
            [first["id"]]
        )

    def test_can_follow_tag_that_has_no_review_yet(self):
        followed = self.client.post(
            "/api/tags/following",
            json={"tag": "History"}
        )

        self.assertEqual(followed.status_code, 201)
        self.assertEqual(self.filtered_reviews("history"), [])

        self.assertEqual(
            self.client.get(
                "/api/tags/following"
            ).get_json()["tags"],
            ["history"]
        )


if __name__ == "__main__":
    unittest.main()
