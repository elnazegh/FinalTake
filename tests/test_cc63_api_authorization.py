
import unittest

from backend.app import app, reviews
from backend.review import Review


class TestCC63ApiAuthorization(unittest.TestCase):

    def setUp(self):
        app.config.update(
            TESTING=True,
            SECRET_KEY="cc63-testing-only-key"
        )
        self.client = app.test_client()

        reviews.clear()
        reviews[1] = Review(
            user_id=1,
            media_id="1",
            rating=4.5,
            text="Original review"
        )

    def tearDown(self):
        reviews.clear()

    def authenticate(self, user_id):
        with self.client.session_transaction() as session:
            session["user_id"] = user_id

    def test_unauthenticated_create_denied(self):
        response = self.client.post(
            "/api/reviews",
            json={
                "media_id": "1",
                "rating": 4.5,
                "text": "Unauthorized review"
            }
        )
        self.assertEqual(response.status_code, 401)

    def test_unauthenticated_edit_denied(self):
        response = self.client.patch(
            "/api/reviews/1",
            json={"text": "Unauthorized edit"}
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(reviews[1].text, "Original review")

    def test_non_owner_edit_denied(self):
        self.authenticate(user_id=2)

        response = self.client.patch(
            "/api/reviews/1",
            json={"text": "Unauthorized edit"}
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(reviews[1].text, "Original review")

    def test_non_owner_delete_denied(self):
        self.authenticate(user_id=2)

        response = self.client.delete("/api/reviews/1")

        self.assertEqual(response.status_code, 403)
        self.assertIn(1, reviews)
        self.assertEqual(reviews[1].text, "Original review")


if __name__ == "__main__":
    unittest.main()
