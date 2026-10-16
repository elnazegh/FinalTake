"""Shared fixtures for tests that need an isolated MySQL database.

Configure a MySQL server the tests may freely create databases on:

    TEST_DB_HOST      (required)
    TEST_DB_USER      (required)
    TEST_DB_PASSWORD  (optional, defaults to empty)
    TEST_DB_PORT      (optional, defaults to 3306)

These are deliberately separate from the DB_* variables used by the app so the
tests can never touch the shared development database. Every test class gets
its own throwaway database (finaltake_test_<random>) that is dropped afterwards.

If the variables are missing or the server is unreachable the tests are skipped,
unless REQUIRE_DB_TESTS=1 is set, in which case they fail instead.
"""

import os
import unittest
import uuid

import mysql.connector

SCHEMA_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "schema.sql"
)
TEST_DB_PREFIX = "finaltake_test_"


def load_server_config():
    host = os.getenv("TEST_DB_HOST")
    user = os.getenv("TEST_DB_USER")

    if not host or not user:
        return None

    return {
        "host": host,
        "port": int(os.getenv("TEST_DB_PORT", "3306")),
        "user": user,
        "password": os.getenv("TEST_DB_PASSWORD", ""),
    }


def _schema_statements():
    with open(SCHEMA_PATH, encoding="utf-8") as schema_file:
        statements = schema_file.read().split(";")

    return [statement.strip() for statement in statements if statement.strip()]


def _unavailable(reason):
    if os.getenv("REQUIRE_DB_TESTS") == "1":
        raise AssertionError(reason)

    raise unittest.SkipTest(reason)


class MySQLTestCase(unittest.TestCase):
    """Creates schema.sql in a disposable database and empties it per test."""

    db_name = None
    _server_config = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        config = load_server_config()

        if config is None:
            _unavailable("TEST_DB_HOST and TEST_DB_USER are not set.")

        try:
            admin = mysql.connector.connect(**config)
        except mysql.connector.Error as error:
            _unavailable(f"Test MySQL server unavailable: {error}")

        cls._server_config = config
        cls.db_name = f"{TEST_DB_PREFIX}{uuid.uuid4().hex[:12]}"

        try:
            cursor = admin.cursor()
            cursor.execute(f"CREATE DATABASE `{cls.db_name}`")
            cursor.execute(f"USE `{cls.db_name}`")

            for statement in _schema_statements():
                cursor.execute(statement)

            admin.commit()
            cursor.close()
        except BaseException:
            admin.close()
            cls._drop_database()
            raise

        admin.close()

    @classmethod
    def tearDownClass(cls):
        try:
            if cls.db_name:
                cls._drop_database()
        finally:
            super().tearDownClass()

    @classmethod
    def _drop_database(cls):
        # Refuse to drop anything that is not a throwaway test database.
        if not cls.db_name.startswith(TEST_DB_PREFIX):
            raise RuntimeError(f"Refusing to drop {cls.db_name!r}.")

        if cls.db_name == os.getenv("DB_NAME"):
            raise RuntimeError("Refusing to drop the configured app database.")

        admin = mysql.connector.connect(**cls._server_config)

        try:
            cursor = admin.cursor()
            cursor.execute(f"DROP DATABASE IF EXISTS `{cls.db_name}`")
            cursor.close()
        finally:
            admin.close()

    @classmethod
    def connect(cls):
        """Open a new strict-mode connection to this class's test database."""
        connection = mysql.connector.connect(
            database=cls.db_name, **cls._server_config
        )

        cursor = connection.cursor()
        cursor.execute("SET SESSION sql_mode = 'STRICT_ALL_TABLES'")
        cursor.close()

        return connection

    def setUp(self):
        super().setUp()

        self.connection = self.connect()
        self.addCleanup(self.connection.close)
        self.addCleanup(self.clear_tables)
        self.clear_tables()

    def clear_tables(self):
        self.connection.rollback()

        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM users")
        self.connection.commit()
        cursor.close()

    def insert_user(
        self,
        username="alice",
        email="alice@example.com",
        password_hash="hash-placeholder",
    ):
        """Insert and commit a user, returning its generated user_id."""
        cursor = self.connection.cursor()
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) "
            "VALUES (%s, %s, %s)",
            (username, email, password_hash),
        )
        self.connection.commit()
        user_id = cursor.lastrowid
        cursor.close()

        return user_id

    def fetch_all(self, sql, params=()):
        cursor = self.connection.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        cursor.close()

        return rows

    def count_users(self):
        return self.fetch_all("SELECT COUNT(*) FROM users")[0][0]
