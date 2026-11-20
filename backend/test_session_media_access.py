import unittest
from unittest.mock import patch

from app import app, reviews


class SessionMediaAccessTests(unittest.TestCase):
    def setUp(self):
        app.config.update(
            TESTING=True,
            SECRET_KEY="session-media-test-key"
        )
        self.client = app.test_client()
        self.review_id = None

    def tearDown(self):
        if self.review_id is not None:
            reviews.pop(self.review_id, None)

    def test_logout_blocks_review_changes_but_preserves_public_access(self):
        with (
            patch(
                "app.get_media_by_id",
                return_value={"id": "1", "title": "The Dark Knight"}
            ),
            patch(
                "app.load_media_titles",
                return_value={"1": "The Dark Knight"}
            ),
            patch("app.get_db_connection"),
            patch(
                "app.get_media",
                return_value={
                    "id": "1",
                    "title": "The Dark Knight",
                    "type": "movie",
                }
            ),
            patch(
                "app.search_media",
                return_value=[
                    {
                        "id": "1",
                        "title": "The Dark Knight",
                        "type": "movie",
                    }
                ]
            )
        ):
            with self.client.session_transaction() as sess:
                sess["user_id"] = 17

            created = self.client.post(
                "/api/reviews",
                json={
                    "media_id": 1,
                    "rating": 4.5,
                    "text": "Session regression test"
                }
            )

            self.assertEqual(created.status_code, 201)
            self.review_id = created.get_json()["review"]["id"]

            logout = self.client.post("/api/auth/logout")
            self.assertEqual(logout.status_code, 200)

            operations = [
                self.client.post(
                    "/api/reviews",
                    json={
                        "media_id": 1,
                        "rating": 5,
                        "text": "Unauthorized review"
                    }
                ),
                self.client.patch(
                    f"/api/reviews/{self.review_id}",
                    json={"text": "Unauthorized edit"}
                ),
                self.client.delete(
                    f"/api/reviews/{self.review_id}"
                )
            ]

            for response in operations:
                with self.subTest(status=response.status_code):
                    self.assertEqual(response.status_code, 401)
                    self.assertEqual(
                        response.get_json()["error"],
                        "Authentication required."
                    )

            self.assertEqual(
                reviews[self.review_id].text,
                "Session regression test"
            )

            self.assertEqual(
                self.client.get("/api/media/1").status_code,
                200
            )

            self.assertEqual(
                self.client.get(
                    "/api/search",
                    query_string={"query": "dark"}
                ).status_code,
                200
            )
