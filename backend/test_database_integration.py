
import os
import unittest
from pathlib import Path
from uuid import uuid4

import mysql.connector

from app import app


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
                cursor.execute(schema_path.read_text().strip())
                connection.commit()
            finally:
                cursor.close()
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


if __name__ == "__main__":
    unittest.main()
