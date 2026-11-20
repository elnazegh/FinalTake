import unittest
from unittest.mock import MagicMock, patch

from app import app
from media import validate_media_payload


VALID_PAYLOAD = {
    "title": "Arrival",
    "type": "movie",
    "releaseYear": 2016,
    "genre": "Science Fiction",
    "imageUrl": "https://example.com/arrival.jpg",
    "description": "First contact story."
}


class CreateMediaApiTests(unittest.TestCase):

    def setUp(self):
        self.original_secret_key = app.config.get("SECRET_KEY")
        app.config.update(
            TESTING=True,
            SECRET_KEY="media-create-tests-only-key"
        )
        self.client = app.test_client()

    def tearDown(self):
        app.config["SECRET_KEY"] = self.original_secret_key

    def login(self, user_id=1):
        with self.client.session_transaction() as session:
            session["user_id"] = user_id

    def mock_connection(self, is_manager=True, lastrowid=7):
        connection = MagicMock()
        cursor = MagicMock()
        cursor.fetchone.return_value = (1,) if is_manager else None
        cursor.lastrowid = lastrowid
        connection.cursor.return_value = cursor

        return connection, cursor

    def insert_calls(self, cursor):
        return [
            call for call in cursor.execute.call_args_list
            if "INSERT INTO media" in call.args[0]
        ]

    @patch("app.get_db_connection")
    def test_successful_creation(self, mock_get_db_connection):
        connection, cursor = self.mock_connection(lastrowid=7)
        mock_get_db_connection.return_value = connection
        self.login()

        response = self.client.post("/api/media", json=VALID_PAYLOAD)

        self.assertEqual(response.status_code, 201)

        body = response.get_json()

        self.assertEqual(body["id"], "7")
        self.assertEqual(body["media"], {
            "id": "7",
            "title": "Arrival",
            "type": "movie",
            "genre": "Science Fiction",
            "imageUrl": "https://example.com/arrival.jpg",
            "releaseYear": 2016,
            "description": "First contact story."
        })

    @patch("app.get_db_connection")
    def test_insert_is_parameterized_and_committed(
        self, mock_get_db_connection
    ):
        connection, cursor = self.mock_connection()
        mock_get_db_connection.return_value = connection
        self.login()

        payload = dict(VALID_PAYLOAD, title="Robert'); DROP TABLE media;--")
        response = self.client.post("/api/media", json=payload)

        self.assertEqual(response.status_code, 201)

        calls = self.insert_calls(cursor)

        self.assertEqual(len(calls), 1)
        self.assertNotIn("DROP TABLE", calls[0].args[0])
        self.assertEqual(
            calls[0].args[1],
            (
                "Robert'); DROP TABLE media;--",
                "movie",
                "Science Fiction",
                "https://example.com/arrival.jpg",
                2016,
                "First contact story."
            )
        )
        connection.commit.assert_called_once()
        connection.rollback.assert_not_called()
        connection.close.assert_called_once()

    @patch("app.get_db_connection")
    def test_optional_fields_can_be_omitted(self, mock_get_db_connection):
        connection, cursor = self.mock_connection()
        mock_get_db_connection.return_value = connection
        self.login()

        response = self.client.post(
            "/api/media",
            json={"title": "  Dune  ", "type": "BOOK"}
        )

        self.assertEqual(response.status_code, 201)

        media = response.get_json()["media"]

        self.assertEqual(media["title"], "Dune")
        self.assertEqual(media["type"], "book")
        self.assertIsNone(media["genre"])
        self.assertIsNone(media["imageUrl"])
        self.assertIsNone(media["releaseYear"])
        self.assertIsNone(media["description"])

    @patch("app.get_db_connection")
    def test_unauthenticated_request_is_rejected(
        self, mock_get_db_connection
    ):
        response = self.client.post("/api/media", json=VALID_PAYLOAD)

        self.assertEqual(response.status_code, 401)
        mock_get_db_connection.assert_not_called()

    @patch("app.get_db_connection")
    def test_authenticated_non_manager_is_forbidden(
        self, mock_get_db_connection
    ):
        connection, cursor = self.mock_connection(is_manager=False)
        mock_get_db_connection.return_value = connection
        self.login()

        response = self.client.post("/api/media", json=VALID_PAYLOAD)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.insert_calls(cursor), [])
        connection.commit.assert_not_called()

    @patch("app.get_db_connection")
    def test_invalid_requests_are_rejected(self, mock_get_db_connection):
        cases = {
            "missing title": {"type": "movie"},
            "blank title": {"title": "   ", "type": "movie"},
            "title too long": {"title": "a" * 256, "type": "movie"},
            "missing type": {"title": "Arrival"},
            "invalid type": {"title": "Arrival", "type": "podcast"},
            "year too early": dict(VALID_PAYLOAD, releaseYear=999),
            "year too late": dict(VALID_PAYLOAD, releaseYear=9999),
            "year not a number": dict(VALID_PAYLOAD, releaseYear="abc"),
            "year boolean": dict(VALID_PAYLOAD, releaseYear=True),
            "year decimal": dict(VALID_PAYLOAD, releaseYear=2016.5),
            "genre too long": dict(VALID_PAYLOAD, genre="g" * 101),
            "genre not text": dict(VALID_PAYLOAD, genre=5),
            "description too long": dict(
                VALID_PAYLOAD, description="d" * 5001
            ),
            "non-web image url": dict(
                VALID_PAYLOAD, imageUrl="javascript:alert(1)"
            ),
            "image url too long": dict(
                VALID_PAYLOAD, imageUrl="https://e.com/" + "a" * 500
            )
        }

        for name, payload in cases.items():
            with self.subTest(name):
                connection, cursor = self.mock_connection()
                mock_get_db_connection.return_value = connection
                self.login()

                response = self.client.post("/api/media", json=payload)

                self.assertEqual(response.status_code, 400)
                self.assertIn("error", response.get_json())
                self.assertEqual(self.insert_calls(cursor), [])
                connection.commit.assert_not_called()

    @patch("app.get_db_connection")
    def test_non_json_body_is_rejected(self, mock_get_db_connection):
        connection, cursor = self.mock_connection()
        mock_get_db_connection.return_value = connection
        self.login()

        response = self.client.post(
            "/api/media",
            data="title=Arrival",
            content_type="application/x-www-form-urlencoded"
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.insert_calls(cursor), [])

    @patch("app.get_db_connection")
    def test_database_connection_failure(self, mock_get_db_connection):
        mock_get_db_connection.side_effect = Exception(
            "secret connection detail"
        )
        self.login()

        response = self.client.post("/api/media", json=VALID_PAYLOAD)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.get_json(),
            {"error": "Unable to create media item."}
        )

    @patch("app.get_db_connection")
    def test_database_insert_failure_rolls_back(
        self, mock_get_db_connection
    ):
        connection, cursor = self.mock_connection()

        def fail_on_insert(query, params=None):
            if "INSERT INTO media" in query:
                raise Exception("secret SQL detail")

        cursor.execute.side_effect = fail_on_insert
        mock_get_db_connection.return_value = connection
        self.login()

        response = self.client.post("/api/media", json=VALID_PAYLOAD)

        self.assertEqual(response.status_code, 500)
        self.assertNotIn("secret", response.get_data(as_text=True))
        connection.rollback.assert_called_once()
        connection.commit.assert_not_called()
        connection.close.assert_called_once()

    @patch("app.get_db_connection")
    def test_permissions_endpoint(self, mock_get_db_connection):
        response = self.client.get("/api/media/permissions")

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.get_json()["canManageMedia"])
        mock_get_db_connection.assert_not_called()

        self.login()

        for is_manager in (True, False):
            with self.subTest(is_manager=is_manager):
                connection, cursor = self.mock_connection(
                    is_manager=is_manager
                )
                mock_get_db_connection.return_value = connection

                response = self.client.get("/api/media/permissions")

                self.assertEqual(response.status_code, 200)
                self.assertEqual(
                    response.get_json()["canManageMedia"], is_manager
                )


class ValidateMediaPayloadTests(unittest.TestCase):

    def test_blank_optional_text_becomes_none(self):
        data = validate_media_payload({
            "title": "Dark",
            "type": "tv",
            "genre": "   ",
            "imageUrl": "",
            "description": ""
        })

        self.assertIsNone(data["genre"])
        self.assertIsNone(data["image_url"])
        self.assertIsNone(data["description"])

    def test_non_object_body_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_media_payload(["title"])


if __name__ == "__main__":
    unittest.main()
