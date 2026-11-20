
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

from backend import app as app_module


class ReviewApiTests(unittest.TestCase):

    def setUp(self):
        self.original_secret_key = app_module.app.config.get("SECRET_KEY")
        app_module.app.config.update(
            TESTING=True,
            SECRET_KEY="review-tests-only-key"
        )

        self.client = app_module.app.test_client()

        app_module.reviews.clear()
        app_module.next_review_id = 1
        self.test_media = {
            "1": {
                "id": "1",
                "title": "The Dark Knight"
            },
            "2": {
                "id": "2",
                "title": "Dark"
            }
        }
        self.media_lookup_patch = patch.object(
            app_module,
            "get_media_by_id",
            side_effect=lambda media_id: self.test_media.get(str(media_id))
        )
        self.media_titles_patch = patch.object(
            app_module,
            "load_media_titles",
            side_effect=lambda media_ids: {
                str(media_id): self.test_media[str(media_id)]["title"]
                for media_id in media_ids
                if str(media_id) in self.test_media
            }
        )
        self.database_connection_patch = patch.object(
            app_module,
            "get_db_connection",
            return_value=MagicMock()
        )
        self.get_media_patch = patch.object(
            app_module,
            "get_media",
            side_effect=lambda connection, media_id:
                self.test_media.get(str(media_id))
        )
        self.media_lookup_patch.start()
        self.media_titles_patch.start()
        self.database_connection_patch.start()
        self.get_media_patch.start()

        # Simulate an authenticated review owner.
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1

    def tearDown(self):
        self.get_media_patch.stop()
        self.database_connection_patch.stop()
        self.media_titles_patch.stop()
        self.media_lookup_patch.stop()
        app_module.app.config["SECRET_KEY"] = self.original_secret_key

    def create_review(
        self,
        user_id=1,
        media_id="1",
        rating=4.5,
        text="Great movie."
    ):
        return self.client.post(
            "/api/reviews",
            json={
                "user_id": user_id,
                "media_id": media_id,
                "rating": rating,
                "text": text
            }
        )

    def test_create_review(self):
        response = self.create_review()

        self.assertEqual(
            response.status_code,
            201
        )

        review = response.get_json()["review"]

        self.assertEqual(
            review["user_id"],
            1
        )

        self.assertEqual(
            review["media_id"],
            "1"
        )

        self.assertEqual(
            review["rating"],
            4.5
        )

        self.assertEqual(
            review["text"],
            "Great movie."
        )

        self.assertEqual(
            review["media_title"],
            "The Dark Knight"
        )

    def test_review_requires_existing_media(self):
        response = self.create_review(
            media_id="999",
            text="Test review."
        )

        self.assertEqual(
            response.status_code,
            404
        )

    def test_invalid_rating_is_rejected(self):
        response = self.create_review(
            rating=3.7,
            text="Test review."
        )

        self.assertEqual(
            response.status_code,
            400
        )

    def test_empty_review_is_rejected(self):
        response = self.create_review(
            text=""
        )

        self.assertEqual(
            response.status_code,
            400
        )

    def test_get_reviews(self):
        self.create_review()

        response = self.client.get(
            "/api/reviews"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        reviews_data = (
            response.get_json()["reviews"]
        )

        self.assertEqual(
            len(reviews_data),
            1
        )

    def test_get_reviews_by_media(self):
        self.create_review()

        response = self.client.get(
            "/api/reviews",
            query_string={
                "media_id": "1"
            }
        )

        self.assertEqual(
            response.status_code,
            200
        )

        reviews_data = (
            response.get_json()["reviews"]
        )

        self.assertEqual(
            len(reviews_data),
            1
        )

        self.assertEqual(
            reviews_data[0]["media_id"],
            "1"
        )

    def test_get_reviews_by_media_excludes_other_media(self):
        self.create_review(
            media_id="1",
            text="Movie review."
        )

        self.create_review(
            media_id="2",
            text="TV review."
        )

        response = self.client.get(
            "/api/reviews",
            query_string={
                "media_id": "1"
            }
        )

        self.assertEqual(
            response.status_code,
            200
        )

        reviews_data = (
            response.get_json()["reviews"]
        )

        self.assertEqual(
            len(reviews_data),
            1
        )

        self.assertEqual(
            reviews_data[0]["media_id"],
            "1"
        )

        self.assertEqual(
            reviews_data[0]["media_title"],
            "The Dark Knight"
        )

        self.assertEqual(
            reviews_data[0]["text"],
            "Movie review."
        )

    def test_owner_can_edit_review(self):
        created = self.create_review()

        review_id = (
            created
            .get_json()["review"]["id"]
        )

        response = self.client.patch(
            f"/api/reviews/{review_id}",
            json={
                "user_id": 1,
                "text": "Updated review."
            }
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertEqual(
            response
            .get_json()["review"]["text"],
            "Updated review."
        )

    def test_non_owner_cannot_edit_review(self):
        created = self.create_review()
        review_id = (
            created
            .get_json()["review"]["id"]
        )

        with self.client.session_transaction() as sess:
            sess["user_id"] = 2

        response = self.client.patch(
            f"/api/reviews/{review_id}",
            json={
                "user_id": 2,
                "text": "Unauthorized edit."
            }
        )

        self.assertEqual(
            response.status_code,
            403
        )

        response = self.client.get(
            f"/api/reviews/{review_id}"
        )

        self.assertEqual(
            response
            .get_json()["review"]["text"],
            "Great movie."
        )

    def test_owner_can_delete_review(self):
        created = self.create_review()

        review_id = (
            created
            .get_json()["review"]["id"]
        )

        response = self.client.delete(
            f"/api/reviews/{review_id}",
            json={
                "user_id": 1
            }
        )

        self.assertEqual(
            response.status_code,
            200
        )

        response = self.client.get(
            f"/api/reviews/{review_id}"
        )

        self.assertEqual(
            response.status_code,
            404
        )

    def test_non_owner_cannot_delete_review(self):
        created = self.create_review()

        review_id = (
            created
            .get_json()["review"]["id"]
        )

        with self.client.session_transaction() as sess:
            sess["user_id"] = 2

        response = self.client.delete(
            f"/api/reviews/{review_id}",
            json={
                "user_id": 2
            }
        )

        self.assertEqual(
            response.status_code,
            403
        )

        response = self.client.get(
            f"/api/reviews/{review_id}"
        )

        self.assertEqual(
            response.status_code,
            200
        )

    def test_review_matches_media_details_api(self):
        # Create a review for The Dark Knight.
        created = self.create_review(
            media_id="1",
            text="Sprint 3 integration test."
        )

        self.assertEqual(created.status_code, 201)

        # Retrieve the media and its reviews separately.
        media_response = self.client.get("/api/media/1")

        reviews_response = self.client.get(
            "/api/reviews",
            query_string={"media_id": "1"}
        )

        # Verify both API requests succeed.
        self.assertEqual(media_response.status_code, 200)
        self.assertEqual(reviews_response.status_code, 200)

        media = media_response.get_json()
        reviews = reviews_response.get_json()["reviews"]

        # Verify the review belongs to the selected media.
        self.assertEqual(len(reviews), 1)
        self.assertEqual(reviews[0]["media_id"], "1")

        # Verify both APIs return the same media title.
        self.assertEqual(
            reviews[0]["media_title"],
            media["title"]
        )

    def test_unauthenticated_cannot_create_review(self):
        anonymous = app_module.app.test_client()

        response = anonymous.post(
            "/api/reviews",
            json={
                "user_id": 1,
                "media_id": "1",
                "rating": 4.5,
                "text": "Unauthorized review."
            }
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(len(app_module.reviews), 0)

    def test_unauthenticated_cannot_edit_review(self):
        created = self.create_review()
        review_id = created.get_json()["review"]["id"]

        anonymous = app_module.app.test_client()

        response = anonymous.patch(
            f"/api/reviews/{review_id}",
            json={
                "user_id": 1,
                "text": "Unauthorized edit."
            }
        )

        self.assertEqual(response.status_code, 401)

        stored_review = self.client.get(
            f"/api/reviews/{review_id}"
        ).get_json()["review"]

        self.assertEqual(
            stored_review["text"],
            "Great movie."
        )

    def test_unauthenticated_cannot_delete_review(self):
        created = self.create_review()
        review_id = created.get_json()["review"]["id"]

        anonymous = app_module.app.test_client()

        response = anonymous.delete(
            f"/api/reviews/{review_id}",
            json={"user_id": 1}
        )

        self.assertEqual(response.status_code, 401)

        remaining = self.client.get(
            f"/api/reviews/{review_id}"
        )

        self.assertEqual(remaining.status_code, 200)

    def test_forged_user_id_does_not_change_review_owner(self):
        response = self.client.post(
            "/api/reviews",
            json={
                "user_id": 99,
                "media_id": "1",
                "rating": 4.5,
                "text": "My review."
            }
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.get_json()["review"]["user_id"],
            1
        )

    def test_non_owner_cannot_edit_using_forged_owner_id(self):
        created = self.create_review()
        review_id = created.get_json()["review"]["id"]

        with self.client.session_transaction() as sess:
            sess["user_id"] = 2

        response = self.client.patch(
            f"/api/reviews/{review_id}",
            json={
                "user_id": 1,
                "text": "Forged edit."
            }
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            app_module.reviews[review_id].text,
            "Great movie."
        )

    def test_non_owner_cannot_delete_using_forged_owner_id(self):
        created = self.create_review()
        review_id = created.get_json()["review"]["id"]

        with self.client.session_transaction() as sess:
            sess["user_id"] = 2

        response = self.client.delete(
            f"/api/reviews/{review_id}",
            json={"user_id": 1}
        )

        self.assertEqual(response.status_code, 403)
        self.assertIn(review_id, app_module.reviews)

    def test_logged_out_user_cannot_modify_or_delete_review(self):
        created = self.create_review()
        review_id = created.get_json()["review"]["id"]

        logout = self.client.post("/api/auth/logout")
        self.assertEqual(logout.status_code, 200)

        session_check = self.client.get("/api/auth/session")
        self.assertEqual(session_check.status_code, 401)

        edit = self.client.patch(
            f"/api/reviews/{review_id}",
            json={
                "user_id": 1,
                "text": "Edit after logout."
            }
        )

        delete = self.client.delete(
            f"/api/reviews/{review_id}",
            json={"user_id": 1}
        )

        self.assertEqual(edit.status_code, 401)
        self.assertEqual(delete.status_code, 401)
        self.assertIn(review_id, app_module.reviews)
        self.assertEqual(
            app_module.reviews[review_id].text,
            "Great movie."
        )

    def test_create_and_retrieve_review_with_tags(self):
        created = self.client.post(
            "/api/reviews",
            json={
                "media_id": "1",
                "rating": 4.5,
                "text": "Great movie.",
                "tags": "Sci Fi, Drama, sci fi"
            }
        )

        self.assertEqual(created.status_code, 201)
        review_data = created.get_json()["review"]
        self.assertEqual(review_data["tags"], ["sci fi", "drama"])

        review_id = review_data["id"]
        retrieved = self.client.get(f"/api/reviews/{review_id}")
        self.assertEqual(retrieved.status_code, 200)
        self.assertEqual(
            retrieved.get_json()["review"]["tags"],
            ["sci fi", "drama"]
        )

        listed = self.client.get("/api/reviews")
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(
            listed.get_json()["reviews"][0]["tags"],
            ["sci fi", "drama"]
        )

    def test_review_without_tags_has_empty_tag_list(self):
        created = self.create_review()
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.get_json()["review"]["tags"], [])

    def test_invalid_tags_rejected_without_creating_review(self):
        response = self.client.post(
            "/api/reviews",
            json={
                "media_id": "1",
                "rating": 4.5,
                "text": "Great movie.",
                "tags": "Drama,,Comedy"
            }
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(app_module.reviews), 0)

    def test_combined_character_limit_enforced_by_api(self):
        response = self.client.post(
            "/api/reviews",
            json={
                "media_id": "1",
                "rating": 4.5,
                "text": "x" * 5000,
                "tags": "drama"
            }
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(app_module.reviews), 0)

    def test_unauthenticated_tagged_review_is_rejected(self):
        anonymous = app_module.app.test_client()
        response = anonymous.post(
            "/api/reviews",
            json={
                "media_id": "1",
                "rating": 4.5,
                "text": "Not logged in.",
                "tags": "drama"
            }
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(len(app_module.reviews), 0)

    def test_forged_user_id_does_not_change_tagged_review_owner(self):
        created = self.client.post(
            "/api/reviews",
            json={
                "user_id": 999,
                "media_id": "1",
                "rating": 4.5,
                "text": "Review with tags.",
                "tags": "drama"
            }
        )
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.get_json()["review"]["user_id"], 1)


if __name__ == "__main__":
    unittest.main()
