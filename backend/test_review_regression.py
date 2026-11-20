import unittest
from unittest.mock import patch

from app import app, media_items


class ReviewRegressionTests(unittest.TestCase):
    def test_edit_preserves_review_media_association(self):
        selected = media_items[0]
        other = next(
            item for item in media_items
            if item["id"] != selected["id"]
        )

        with patch.dict(app.config, {
            "TESTING": True,
            "SECRET_KEY": "review-regression-test-key"
        }):
            with (
                patch("app.reviews", {}),
                patch("app.next_review_id", 1),
                patch("app.get_media_by_id", return_value=selected),
                patch(
                    "app.load_media_titles",
                    return_value={
                        item["id"]: item["title"]
                        for item in media_items
                    }
                )
            ):
                client = app.test_client()

                with client.session_transaction() as session:
                    session["user_id"] = 17

                created = client.post(
                    "/api/reviews",
                    json={
                        "media_id": selected["id"],
                        "rating": 4.5,
                        "text": "Original regression review"
                    }
                )

                self.assertEqual(created.status_code, 201)

                original = created.get_json()["review"]
                review_id = original["id"]

                updated = client.patch(
                    f"/api/reviews/{review_id}",
                    json={"text": "Updated regression review"}
                )

                self.assertEqual(updated.status_code, 200)

                retrieved = client.get(
                    f"/api/reviews/{review_id}"
                )

                self.assertEqual(retrieved.status_code, 200)

                review = retrieved.get_json()["review"]

                self.assertEqual(
                    review["text"],
                    "Updated regression review"
                )
                self.assertEqual(
                    review["media_id"],
                    original["media_id"]
                )
                self.assertEqual(
                    review["media_title"],
                    original["media_title"]
                )

                selected_reviews = client.get(
                    "/api/reviews",
                    query_string={"media_id": selected["id"]}
                ).get_json()["reviews"]

                other_reviews = client.get(
                    "/api/reviews",
                    query_string={"media_id": other["id"]}
                ).get_json()["reviews"]

                self.assertTrue(
                    any(item["id"] == review_id for item in selected_reviews)
                )
                self.assertFalse(
                    any(item["id"] == review_id for item in other_reviews)
                )
