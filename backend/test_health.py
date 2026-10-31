import unittest
from unittest.mock import patch

from app import app


class HealthApiTests(unittest.TestCase):

    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_database_error_does_not_expose_internal_details(self):
        private_error = "internal-db-host:3306 connection refused"

        with patch(
            "app.get_db_connection",
            side_effect=RuntimeError(private_error)
        ):
            with patch.object(app.logger, "exception") as log_exception:
                response = self.client.get("/api/health")

        self.assertEqual(response.status_code, 500)

        self.assertEqual(
            response.get_json(),
            {
                "status": "unhealthy",
                "database": "disconnected"
            }
        )

        self.assertNotIn(
            private_error,
            response.get_data(as_text=True)
        )

        log_exception.assert_called_once_with("Health check failed")


if __name__ == "__main__":
    unittest.main()
