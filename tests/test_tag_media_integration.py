import unittest
from backend import app as app_module

@unittest.skipUnless(
    hasattr(app_module, "normalize_tags"),
    "Tags functionality is not yet available on this branch"
)
class TagMediaIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.original_secret_key = app_module.app.config.get("SECRET_KEY")
        self.original_testing = app_module.app.config.get("TESTING")
        self.original_reviews = app_module.reviews.copy()
        self.original_next_review_id = app_module.next_review_id

        app_module.app.config.update(
            TESTING=True,
            SECRET_KEY="tag-media-integration-test"
        )
        app_module.reviews.clear()
        app_module.next_review_id = 1

        self.client = app_module.app.test_client()

        with self.client.session_transaction() as sess:
            sess["user_id"] = 1

    def tearDown(self):
        app_module.reviews.clear()
        app_module.reviews.update(self.original_reviews)
        app_module.next_review_id = self.original_next_review_id
        app_module.app.config["SECRET_KEY"] = self.original_secret_key
        app_module.app.config["TESTING"] = self.original_testing

    def test_tag_discovery_matches_media_details_and_search(self):
        for media_id in ("1", "4"):
            response = self.client.post(
                "/api/reviews",
                json={
                    "media_id": media_id,
                    "rating": 4.5,
                    "text": "Tag integration test.",
                    "tags": "Discovery, QA"
                }
            )
            self.assertEqual(response.status_code, 201)

        response = self.client.get(
            "/api/reviews",
            query_string={"tag": "DISCOVERY"}
        )
        self.assertEqual(response.status_code, 200)

        tagged_reviews = response.get_json()["reviews"]
        self.assertEqual(len(tagged_reviews), 2)
        self.assertEqual(
            {review["media_id"] for review in tagged_reviews},
            {"1", "4"}
        )

        for review in tagged_reviews:
            media_response = self.client.get(
                f"/api/media/{review['media_id']}"
            )
            self.assertEqual(media_response.status_code, 200)

            media = media_response.get_json()
            self.assertEqual(review["media_id"], media["id"])
            self.assertEqual(review["media_title"], media["title"])
            self.assertIn("discovery", review["tags"])

            search_response = self.client.get(
                "/api/search",
                query_string={"query": media["title"]}
            )
            self.assertEqual(search_response.status_code, 200)
            self.assertIn(
                media["id"],
                [
                    result["id"]
                    for result in search_response.get_json()["results"]
                ]
            )

if __name__ == "__main__":
    unittest.main()
