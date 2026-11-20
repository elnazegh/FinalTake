
import os
import unittest
from pathlib import Path
from uuid import uuid4

import mysql.connector

from app import app
from seed_media import DEMO_MEDIA, seed_demo_media


@unittest.skipUnless(
    os.getenv("RUN_MYSQL_INTEGRATION_TESTS") == "1",
    "Requires isolated CI MySQL test database",
)
class MySQLDatabaseIntegrationTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Safety guard: never run against the team's actual database.
        if os.getenv("DB_NAME") != "finaltake_ci_test":
            raise RuntimeError(
                "Integration tests require DB_NAME=finaltake_ci_test"
            )

        cls.db_config = {
            "host": os.environ["DB_HOST"],
            "user": os.environ["DB_USER"],
            "password": os.environ["DB_PASSWORD"],
            "database": os.environ["DB_NAME"],
        }

        # Prepare the existing schema in the disposable test database.
        connection = mysql.connector.connect(**cls.db_config)
        try:
            cursor = connection.cursor()
            try:
                schema_path = Path(__file__).with_name("schema.sql")

                # Execute each SQL statement separately
                sql_statements = schema_path.read_text().split(";")

                for statement in sql_statements:
                    statement = statement.strip()

                    if statement:
                        cursor.execute(statement)

                connection.commit()
                seed_demo_media(connection)
            finally:
                cursor.close()
        finally:
            connection.close()

    def test_demo_media_seed_is_idempotent_and_preserves_ids(self):
        connection = mysql.connector.connect(**self.db_config)

        try:
            cursor = connection.cursor()
            try:
                schema_path = Path(__file__).with_name("schema.sql")

                for statement in schema_path.read_text().split(";"):
                    statement = statement.strip()

                    if statement:
                        cursor.execute(statement)

                connection.commit()
            finally:
                cursor.close()

            inserted_first = seed_demo_media(connection)
            inserted_second = seed_demo_media(connection)

            self.assertEqual(inserted_first, 0)
            self.assertEqual(inserted_second, 0)

            cursor = connection.cursor()
            try:
                cursor.execute(
                    """
                    SELECT media_id, title, media_type
                    FROM media
                    WHERE media_id BETWEEN 1 AND 5
                    ORDER BY media_id
                    """
                )
                rows = cursor.fetchall()
            finally:
                cursor.close()

            self.assertEqual(len(rows), len(DEMO_MEDIA))
            self.assertEqual(
                [(row[0], row[1], row[2]) for row in rows],
                [
                    (
                        item["media_id"],
                        item["title"],
                        item["media_type"]
                    )
                    for item in DEMO_MEDIA
                ]
            )

            client = app.test_client()
            catalog_response = client.get("/api/media")
            details_response = client.get("/api/media/4")
            search_response = client.get(
                "/api/search",
                query_string={"query": "DUNE"}
            )

            self.assertEqual(catalog_response.status_code, 200)
            self.assertEqual(
                [item["id"] for item in catalog_response.get_json()["media"]
                 if int(item["id"]) <= 5],
                ["1", "2", "3", "4", "5"]
            )
            self.assertEqual(details_response.status_code, 200)
            self.assertEqual(details_response.get_json()["title"], "Dune")
            self.assertEqual(search_response.status_code, 200)
            self.assertEqual(
                search_response.get_json()["results"][0]["id"],
                "4"
            )

        finally:
            connection.close()

    def test_registration_persists_user_in_mysql(self):
        username = f"ci_{uuid4().hex[:12]}"
        email = f"{username}@example.com"
        password = "IntegrationTest123!"

        app.config["TESTING"] = True
        client = app.test_client()

        try:
            # DB-02: Create a user through the real Flask API.
            response = client.post(
                "/api/auth/register",
                json={
                    "username": username,
                    "email": email,
                    "password": password,
                },
            )

            self.assertEqual(response.status_code, 201)

            # DB-01: Retrieve it through a NEW MySQL connection.
            connection = mysql.connector.connect(**self.db_config)
            try:
                cursor = connection.cursor()
                try:
                    cursor.execute(
                        """
                        SELECT username, email, password_hash
                        FROM users
                        WHERE username = %s
                        """,
                        (username,),
                    )
                    record = cursor.fetchone()
                finally:
                    cursor.close()
            finally:
                connection.close()

            self.assertIsNotNone(record)
            self.assertEqual(record[0], username)
            self.assertEqual(record[1], email)
            self.assertNotEqual(record[2], password)
            self.assertTrue(len(record[2]) > 20)

        finally:
            # Remove the test user from the disposable database.
            connection = mysql.connector.connect(**self.db_config)
            try:
                cursor = connection.cursor()
                try:
                    cursor.execute(
                        "DELETE FROM users WHERE username = %s",
                        (username,),
                    )
                    connection.commit()
                finally:
                    cursor.close()
            finally:
                connection.close()


    def test_media_creation_persists_in_mysql(self):
        username = f"ci_{uuid4().hex[:12]}"
        title = f"Integration Media {uuid4().hex[:8]}"
        user_id = None
        media_id = None

        connection = mysql.connector.connect(**self.db_config)
        try:
            cursor = connection.cursor()
            try:
                # Create a user and grant it media management permission.
                cursor.execute(
                    """
                    INSERT INTO users (username, email, password_hash)
                    VALUES (%s, %s, %s)
                    """,
                    (username, f"{username}@example.com", "unused-hash"),
                )
                user_id = cursor.lastrowid
                cursor.execute(
                    "INSERT INTO media_managers (user_id) VALUES (%s)",
                    (user_id,),
                )
                connection.commit()
            finally:
                cursor.close()
        finally:
            connection.close()

        original_secret_key = app.config.get("SECRET_KEY")
        app.config["TESTING"] = True
        app.config["SECRET_KEY"] = "media-integration-tests-only-key"

        try:
            client = app.test_client()

            with client.session_transaction() as session:
                session["user_id"] = user_id

            response = client.post(
                "/api/media",
                json={
                    "title": title,
                    "type": "game",
                    "releaseYear": 2011,
                    "genre": "RPG",
                    "description": "Persistence check.",
                },
            )

            self.assertEqual(response.status_code, 201)
            media_id = int(response.get_json()["id"])
            self.assertGreater(media_id, 5)

            # Retrieve the record through a NEW MySQL connection.
            connection = mysql.connector.connect(**self.db_config)
            try:
                cursor = connection.cursor()
                try:
                    cursor.execute(
                        """
                        SELECT title, media_type, genre, image_url,
                               release_year, description, created_at
                        FROM media
                        WHERE media_id = %s
                        """,
                        (media_id,),
                    )
                    record = cursor.fetchone()
                finally:
                    cursor.close()
            finally:
                connection.close()

            self.assertIsNotNone(record)
            self.assertEqual(record[0], title)
            self.assertEqual(record[1], "game")
            self.assertEqual(record[2], "RPG")
            self.assertIsNone(record[3])
            self.assertEqual(record[4], 2011)
            self.assertEqual(record[5], "Persistence check.")
            self.assertIsNotNone(record[6])

            details_response = client.get(f"/api/media/{media_id}")
            self.assertEqual(details_response.status_code, 200)
            self.assertEqual(
                details_response.get_json()["title"],
                title
            )

            list_response = client.get("/api/media")
            self.assertEqual(list_response.status_code, 200)
            self.assertIn(
                str(media_id),
                [item["id"] for item in list_response.get_json()["media"]]
            )

            search_response = client.get(
                "/api/search",
                query_string={"query": title, "media_type": "game"}
            )
            self.assertEqual(search_response.status_code, 200)
            self.assertEqual(
                search_response.get_json()["results"][0]["id"],
                str(media_id)
            )

        finally:
            app.config["SECRET_KEY"] = original_secret_key

            # Remove test data from the disposable database.
            connection = mysql.connector.connect(**self.db_config)
            try:
                cursor = connection.cursor()
                try:
                    if media_id is not None:
                        cursor.execute(
                            "DELETE FROM media WHERE media_id = %s",
                            (media_id,),
                        )

                    # media_managers rows are removed by ON DELETE CASCADE.
                    cursor.execute(
                        "DELETE FROM users WHERE user_id = %s",
                        (user_id,),
                    )
                    connection.commit()
                finally:
                    cursor.close()
            finally:
                connection.close()

    def test_media_not_created_for_non_manager_in_mysql(self):
        username = f"ci_{uuid4().hex[:12]}"
        title = f"Unauthorized Media {uuid4().hex[:8]}"

        connection = mysql.connector.connect(**self.db_config)
        try:
            cursor = connection.cursor()
            try:
                cursor.execute(
                    """
                    INSERT INTO users (username, email, password_hash)
                    VALUES (%s, %s, %s)
                    """,
                    (username, f"{username}@example.com", "unused-hash"),
                )
                user_id = cursor.lastrowid
                connection.commit()
            finally:
                cursor.close()
        finally:
            connection.close()

        original_secret_key = app.config.get("SECRET_KEY")
        app.config["TESTING"] = True
        app.config["SECRET_KEY"] = "media-integration-tests-only-key"

        try:
            client = app.test_client()

            with client.session_transaction() as session:
                session["user_id"] = user_id

            response = client.post(
                "/api/media",
                json={"title": title, "type": "movie"},
            )

            self.assertEqual(response.status_code, 403)

            connection = mysql.connector.connect(**self.db_config)
            try:
                cursor = connection.cursor()
                try:
                    cursor.execute(
                        "SELECT COUNT(*) FROM media WHERE title = %s",
                        (title,),
                    )
                    self.assertEqual(cursor.fetchone()[0], 0)
                finally:
                    cursor.close()
            finally:
                connection.close()

        finally:
            app.config["SECRET_KEY"] = original_secret_key

            connection = mysql.connector.connect(**self.db_config)
            try:
                cursor = connection.cursor()
                try:
                    cursor.execute(
                        "DELETE FROM users WHERE user_id = %s",
                        (user_id,),
                    )
                    connection.commit()
                finally:
                    cursor.close()
            finally:
                connection.close()


if __name__ == "__main__":
    unittest.main()
