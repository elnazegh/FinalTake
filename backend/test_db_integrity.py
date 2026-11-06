"""Sprint 3 database integrity and CRUD tests for the MySQL `users` table.

These run against a disposable database (see db_test_support.py) and are
skipped when no test MySQL server is configured.
"""

import unittest

from mysql.connector import errors

from db_test_support import MySQLTestCase

ER_DUP_ENTRY = 1062
ER_BAD_NULL_ERROR = 1048


def _text(value):
    if isinstance(value, (bytes, bytearray)):
        return value.decode()

    return value


class UserCrudTests(MySQLTestCase):

    def test_insert_returns_generated_user_id(self):
        user_id = self.insert_user()

        self.assertGreater(user_id, 0)

    def test_inserted_user_can_be_read_back(self):
        user_id = self.insert_user("bob", "bob@example.com", "hash-bob")

        rows = self.fetch_all(
            "SELECT user_id, username, email, password_hash "
            "FROM users WHERE user_id = %s",
            (user_id,),
        )

        self.assertEqual(
            rows, [(user_id, "bob", "bob@example.com", "hash-bob")]
        )

    def test_user_ids_are_unique_and_increasing(self):
        first = self.insert_user("u1", "u1@example.com")
        second = self.insert_user("u2", "u2@example.com")

        self.assertGreater(second, first)

    def test_reading_nonexistent_user_returns_no_rows(self):
        rows = self.fetch_all("SELECT * FROM users WHERE user_id = %s", (999999,))

        self.assertEqual(rows, [])

    def test_update_changes_only_the_target_row(self):
        target = self.insert_user("target", "target@example.com")
        other = self.insert_user("other", "other@example.com")

        cursor = self.connection.cursor()
        cursor.execute(
            "UPDATE users SET email = %s WHERE user_id = %s",
            ("new@example.com", target),
        )
        self.connection.commit()
        self.assertEqual(cursor.rowcount, 1)
        cursor.close()

        emails = dict(self.fetch_all("SELECT user_id, email FROM users"))

        self.assertEqual(emails[target], "new@example.com")
        self.assertEqual(emails[other], "other@example.com")

    def test_update_of_nonexistent_user_affects_no_rows(self):
        cursor = self.connection.cursor()
        cursor.execute(
            "UPDATE users SET email = %s WHERE user_id = %s",
            ("ghost@example.com", 999999),
        )
        self.connection.commit()

        self.assertEqual(cursor.rowcount, 0)
        cursor.close()

    def test_delete_removes_only_the_target_user(self):
        target = self.insert_user("target", "target@example.com")
        self.insert_user("keeper", "keeper@example.com")

        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM users WHERE user_id = %s", (target,))
        self.connection.commit()
        self.assertEqual(cursor.rowcount, 1)
        cursor.close()

        usernames = [row[0] for row in self.fetch_all("SELECT username FROM users")]

        self.assertEqual(usernames, ["keeper"])

    def test_delete_of_nonexistent_user_affects_no_rows(self):
        self.insert_user()

        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM users WHERE user_id = %s", (999999,))
        self.connection.commit()

        self.assertEqual(cursor.rowcount, 0)
        self.assertEqual(self.count_users(), 1)
        cursor.close()

    def test_username_and_email_can_be_reused_after_delete(self):
        user_id = self.insert_user("reuse", "reuse@example.com")

        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
        self.connection.commit()
        cursor.close()

        new_id = self.insert_user("reuse", "reuse@example.com")

        self.assertNotEqual(new_id, user_id)


class UserConstraintTests(MySQLTestCase):

    def assert_insert_fails(self, error_type, errno, username, email, password_hash):
        with self.assertRaises(error_type) as context:
            self.insert_user(username, email, password_hash)

        if errno is not None:
            self.assertEqual(context.exception.errno, errno)

    def test_duplicate_username_is_rejected(self):
        self.insert_user("dupe", "first@example.com")

        self.assert_insert_fails(
            errors.IntegrityError, ER_DUP_ENTRY,
            "dupe", "second@example.com", "hash",
        )

    def test_duplicate_email_is_rejected(self):
        self.insert_user("first", "dupe@example.com")

        self.assert_insert_fails(
            errors.IntegrityError, ER_DUP_ENTRY,
            "second", "dupe@example.com", "hash",
        )

    def test_duplicate_primary_key_is_rejected(self):
        user_id = self.insert_user()
        cursor = self.connection.cursor()

        with self.assertRaises(errors.IntegrityError) as context:
            cursor.execute(
                "INSERT INTO users (user_id, username, email, password_hash) "
                "VALUES (%s, 'x', 'x@example.com', 'h')",
                (user_id,),
            )

        self.assertEqual(context.exception.errno, ER_DUP_ENTRY)
        cursor.close()

    def test_update_to_existing_email_is_rejected(self):
        self.insert_user("one", "one@example.com")
        second = self.insert_user("two", "two@example.com")
        cursor = self.connection.cursor()

        with self.assertRaises(errors.IntegrityError) as context:
            cursor.execute(
                "UPDATE users SET email = 'one@example.com' WHERE user_id = %s",
                (second,),
            )

        self.assertEqual(context.exception.errno, ER_DUP_ENTRY)
        cursor.close()

    def test_null_values_are_rejected_for_every_required_column(self):
        valid = {
            "username": "nullable",
            "email": "nullable@example.com",
            "password_hash": "hash",
        }

        for column in valid:
            with self.subTest(column=column):
                values = {**valid, column: None}

                self.assert_insert_fails(
                    errors.IntegrityError, ER_BAD_NULL_ERROR,
                    values["username"], values["email"], values["password_hash"],
                )

        self.assertEqual(self.count_users(), 0)

    def test_username_length_boundary(self):
        self.insert_user("u" * 50, "fifty@example.com")

        with self.assertRaises(errors.DataError):
            self.insert_user("u" * 51, "fifty-one@example.com")

    def test_email_length_boundary(self):
        long_email = "e" * 243 + "@example.com"
        self.assertEqual(len(long_email), 255)

        self.insert_user("max-email", long_email)

        with self.assertRaises(errors.DataError):
            self.insert_user("over-email", "e" + long_email)

    def test_password_hash_length_boundary(self):
        self.insert_user("max-hash", "max-hash@example.com", "h" * 255)

        with self.assertRaises(errors.DataError):
            self.insert_user("over-hash", "over-hash@example.com", "h" * 256)


class FailedOperationConsistencyTests(MySQLTestCase):

    def test_failed_insert_leaves_existing_rows_unchanged(self):
        self.insert_user("keeper", "keeper@example.com", "original")

        with self.assertRaises(errors.IntegrityError):
            self.insert_user("keeper", "other@example.com", "different")

        rows = self.fetch_all("SELECT username, email, password_hash FROM users")

        self.assertEqual(rows, [("keeper", "keeper@example.com", "original")])

    def test_rollback_discards_earlier_inserts_in_a_failed_transaction(self):
        self.insert_user("existing", "existing@example.com")
        cursor = self.connection.cursor()

        cursor.execute(
            "INSERT INTO users (username, email, password_hash) "
            "VALUES ('new', 'new@example.com', 'h')"
        )

        with self.assertRaises(errors.IntegrityError):
            cursor.execute(
                "INSERT INTO users (username, email, password_hash) "
                "VALUES ('existing', 'dup@example.com', 'h')"
            )

        self.connection.rollback()
        cursor.close()

        usernames = [row[0] for row in self.fetch_all("SELECT username FROM users")]

        self.assertEqual(usernames, ["existing"])

    def test_failed_update_keeps_original_value(self):
        self.insert_user("one", "one@example.com")
        second = self.insert_user("two", "two@example.com")
        cursor = self.connection.cursor()

        with self.assertRaises(errors.IntegrityError):
            cursor.execute(
                "UPDATE users SET email = 'one@example.com' WHERE user_id = %s",
                (second,),
            )

        self.connection.rollback()
        cursor.close()

        rows = self.fetch_all(
            "SELECT email FROM users WHERE user_id = %s", (second,)
        )

        self.assertEqual(rows, [("two@example.com",)])

    def test_uncommitted_insert_is_not_visible_to_other_connections(self):
        cursor = self.connection.cursor()
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) "
            "VALUES ('pending', 'pending@example.com', 'h')"
        )

        other = self.connect()
        self.addCleanup(other.close)
        other_cursor = other.cursor()
        other_cursor.execute("SELECT COUNT(*) FROM users")
        visible = other_cursor.fetchone()[0]
        other_cursor.close()

        self.connection.rollback()
        cursor.close()

        self.assertEqual(visible, 0)
        self.assertEqual(self.count_users(), 0)

    def test_sql_metacharacters_are_stored_as_literal_text(self):
        hostile = "x'; DROP TABLE users; --"
        self.insert_user(hostile, "hostile@example.com")

        rows = self.fetch_all(
            "SELECT username FROM users WHERE email = %s", ("hostile@example.com",)
        )

        self.assertEqual(rows, [(hostile,)])


class SchemaDefinitionTests(MySQLTestCase):
    """schema.sql currently defines only `users`; it has no foreign keys."""

    def test_users_table_columns_and_keys(self):
        rows = self.fetch_all(
            "SELECT column_name, is_nullable, column_key "
            "FROM information_schema.columns "
            "WHERE table_schema = %s AND table_name = 'users'",
            (self.db_name,),
        )

        columns = {
            _text(name): (_text(nullable), _text(key))
            for name, nullable, key in rows
        }

        self.assertEqual(
            columns,
            {
                "user_id": ("NO", "PRI"),
                "username": ("NO", "UNI"),
                "email": ("NO", "UNI"),
                "password_hash": ("NO", ""),
            },
        )

    def test_schema_defines_only_the_users_table(self):
        rows = self.fetch_all(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = %s",
            (self.db_name,),
        )

        self.assertEqual([_text(row[0]) for row in rows], ["users"])


if __name__ == "__main__":
    unittest.main()
