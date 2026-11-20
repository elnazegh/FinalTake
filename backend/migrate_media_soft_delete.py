"""Explicit, repeatable migration for media soft deletion."""

import sys

try:
    from .database import get_db_connection
except ImportError:
    from database import get_db_connection


def migrate_media_soft_delete(connection):
    """Inspect media constraints and add a nullable deletion marker if absent."""
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT TABLE_NAME FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s",
            ("media",)
        )
        if cursor.fetchone() is None:
            raise RuntimeError("The media table does not exist. Apply schema.sql first.")

        cursor.execute(
            "SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME, CONSTRAINT_NAME, "
            "REFERENCED_TABLE_SCHEMA, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME "
            "FROM information_schema.KEY_COLUMN_USAGE "
            "WHERE REFERENCED_TABLE_NAME IS NOT NULL AND "
            "((TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s) OR "
            "(REFERENCED_TABLE_SCHEMA = DATABASE() AND REFERENCED_TABLE_NAME = %s))",
            ("media", "media")
        )
        constraints = cursor.fetchall()

        cursor.execute(
            "SELECT DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT, EXTRA "
            "FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() "
            "AND TABLE_NAME = %s AND COLUMN_NAME = %s",
            ("media", "deleted_at")
        )
        column = cursor.fetchone()
        if column is not None:
            if (
                column["DATA_TYPE"].lower() != "timestamp"
                or column["IS_NULLABLE"] != "YES"
                or column["COLUMN_DEFAULT"] is not None
                or "on update" in column["EXTRA"].lower()
            ):
                raise RuntimeError(
                    "Existing media.deleted_at is incompatible; inspect it "
                    "manually before deploying."
                )
            return False, constraints

        cursor.execute(
            "ALTER TABLE media ADD COLUMN deleted_at TIMESTAMP NULL DEFAULT NULL"
        )
        return True, constraints
    finally:
        cursor.close()


def main():
    connection = None
    try:
        connection = get_db_connection()
        added, constraints = migrate_media_soft_delete(connection)
        print("Media foreign-key constraints inspected:")
        if constraints:
            for constraint in constraints:
                print(
                    f"  {constraint['CONSTRAINT_NAME']}: "
                    f"{constraint['TABLE_SCHEMA']}.{constraint['TABLE_NAME']}."
                    f"{constraint['COLUMN_NAME']} -> "
                    f"{constraint['REFERENCED_TABLE_SCHEMA']}."
                    f"{constraint['REFERENCED_TABLE_NAME']}."
                    f"{constraint['REFERENCED_COLUMN_NAME']}"
                )
        else:
            print("  None found.")
        print("Added deleted_at." if added else "deleted_at already present.")
        return 0
    except Exception as error:
        print(f"Media migration failed: {error}", file=sys.stderr)
        return 1
    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
