import os
import secrets
import subprocess
import sys
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

import mysql.connector
import test_database_integration
from app import app, reviews
from media import delete_media_record
from migrate_media_soft_delete import migrate_media_soft_delete
from seed_media import seed_demo_media


@unittest.skipUnless(os.getenv("RUN_MYSQL_INTEGRATION_TESTS") == "1",
                     "Requires isolated CI MySQL test database")
class DeleteIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        test_database_integration.MySQLDatabaseIntegrationTests.setUpClass.__func__(cls)

    def setUp(self):
        self.conn = mysql.connector.connect(**self.db_config)
        self.cursor = self.conn.cursor()
        self.media_ids = []
        self.review_ids = []
        self.secret_key = app.config.get("SECRET_KEY")
        app.config["SECRET_KEY"] = secrets.token_hex(32)
        name = f"ci_{uuid4().hex[:12]}"
        self.cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
            (name, f"{name}@example.com", "unused-hash"),
        )
        self.user_id = self.cursor.lastrowid
        self.cursor.execute(
            "INSERT INTO media_managers (user_id) VALUES (%s)", (self.user_id,)
        )
        self.conn.commit()
        self.client = app.test_client()
        with self.client.session_transaction() as session:
            session["user_id"] = self.user_id

    def tearDown(self):
        app.config["SECRET_KEY"] = self.secret_key
        for review_id in self.review_ids:
            reviews.pop(review_id, None)
        for media_id in self.media_ids:
            self.cursor.execute("DELETE FROM media WHERE media_id = %s", (media_id,))
        self.cursor.execute("DELETE FROM users WHERE user_id = %s", (self.user_id,))
        self.conn.commit()
        self.cursor.close()
        self.conn.close()

    def create_media(self, title):
        response = self.client.post("/api/media", json={
            "title": title, "type": "movie", "releaseYear": 2026,
            "genre": "Adventure",
        })
        self.assertEqual(response.status_code, 201)
        media_id = int(response.get_json()["id"])
        self.media_ids.append(media_id)
        self.assertGreater(media_id, 5)
        return media_id

    def test_soft_delete_preserves_row_and_related_review(self):
        title = f"Delete integration {uuid4().hex[:12]}"
        media_id = self.create_media(title)
        review = self.client.post("/api/reviews", json={
            "media_id": media_id, "rating": 4.5, "text": "Preserve me",
            "tags": ["adventure"],
        })
        self.assertEqual(review.status_code, 201)
        review_id = review.get_json()["review"]["id"]
        self.review_ids.append(review_id)
        self.assertEqual(self.client.delete(f"/api/media/{media_id}").status_code, 200)
        self.assertEqual(self.client.delete(f"/api/media/{media_id}").status_code, 404)
        self.assertEqual(self.client.get(f"/api/media/{media_id}").status_code, 404)
        code = (
            "import sys; from app import app; c = app.test_client(); "
            "assert c.get('/api/media/' + sys.argv[1]).status_code == 404; "
            "assert c.get('/api/search', query_string={'query': sys.argv[2]})"
            ".get_json()['results'] == []"
        )
        for _ in range(2):
            subprocess.run(
                [sys.executable, "-c", code, str(media_id), title],
                cwd=Path(__file__).parent, check=True, capture_output=True, text=True,
            )
        self.assertEqual(self.client.patch(
            f"/api/media/{media_id}", json={"genre": "Drama"}
        ).status_code, 404)
        self.assertEqual(self.client.post("/api/reviews", json={
            "media_id": media_id, "rating": 4, "text": "New review",
        }).status_code, 404)
        self.assertNotIn(str(media_id), [
            row["id"] for row in self.client.get("/api/media").get_json()["media"]
        ])
        self.assertEqual(self.client.get(
            "/api/search", query_string={"query": title}
        ).get_json()["results"], [])
        retained = self.client.get(f"/api/reviews/{review_id}")
        self.assertEqual(retained.status_code, 200)
        self.assertEqual(retained.get_json()["review"]["media_title"], title)
        self.assertEqual(retained.get_json()["review"]["tags"], ["adventure"])
        with mysql.connector.connect(**self.db_config) as fresh:
            cursor = fresh.cursor()
            cursor.execute(
                "SELECT media_id, title, deleted_at FROM media WHERE media_id = %s",
                (media_id,),
            )
            row = cursor.fetchone()
            cursor.close()
            self.assertEqual(row[:2], (media_id, title))
            self.assertIsNotNone(row[2])
            self.assertEqual(seed_demo_media(fresh), 0)
            self.assertFalse(migrate_media_soft_delete(fresh)[0])
        self.assertEqual(self.client.get(f"/api/media/{media_id}").status_code, 404)

    def test_concurrent_soft_deletes_only_succeed_once(self):
        media_id = self.create_media(f"Concurrent delete {uuid4().hex[:12]}")

        def delete(_):
            with mysql.connector.connect(**self.db_config) as connection:
                return delete_media_record(connection, media_id)

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(delete, range(2)))
        self.assertEqual(sorted(outcomes), [False, True])
