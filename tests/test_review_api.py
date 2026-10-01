import unittest

from backend import app as app_module


class ReviewApiTests(unittest.TestCase):

    def setUp(self):
        app_module.app.config["TESTING"] = True
        self.client = app_module.app.test_client()

        app_module.reviews.clear()
        app_module.next_review_id = 1

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


if __name__ == "__main__":
    unittest.main()