"""Optional MySQL-backed storage for FinalTake reviews.

This module deliberately does not import Flask. The existing in-memory routes
remain available for unit tests and demos until MySQL storage is enabled.
"""

import json

try:
    from .review import Review
except ImportError:
    from review import Review


class MySQLReviewStore:
    """Store and retrieve the existing Review model without changing API fields."""

    def __init__(self, connection_factory):
        self.connection_factory = connection_factory

    @staticmethod
    def _decode_review(row):
        tags_json = row["tags_json"]
        if isinstance(tags_json, (str, bytes, bytearray)):
            tags = json.loads(tags_json)
        else:
            tags = tags_json
        return Review(
            user_id=row["user_id"],
            media_id=str(row["media_id"]),
            rating=float(row["rating"]),
            text=row["review_text"],
            tags=tags,
        )

    def create(self, review):
        connection = self.connection_factory()
        cursor = None
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO reviews
                    (user_id, media_id, rating, review_text, tags_json)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    review.user_id,
                    str(review.media_id),
                    review.rating,
                    review.text,
                    json.dumps(review.tags),
                ),
            )
            review_id = cursor.lastrowid
            connection.commit()
            return review_id
        except Exception:
            connection.rollback()
            raise
        finally:
            if cursor is not None:
                cursor.close()
            connection.close()

    def get(self, review_id):
        connection = self.connection_factory()
        cursor = None
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT review_id, user_id, media_id, rating,
                       review_text, tags_json
                FROM reviews
                WHERE review_id = %s
                """,
                (review_id,),
            )
            row = cursor.fetchone()
            return self._decode_review(row) if row is not None else None
        finally:
            if cursor is not None:
                cursor.close()
            connection.close()

    def list(self, media_id=None, tag=None):
        connection = self.connection_factory()
        cursor = None
        try:
            cursor = connection.cursor(dictionary=True)
            if media_id is None:
                cursor.execute(
                    """
                    SELECT review_id, user_id, media_id, rating,
                           review_text, tags_json
                    FROM reviews
                    ORDER BY review_id
                    """
                )
            else:
                cursor.execute(
                    """
                    SELECT review_id, user_id, media_id, rating,
                           review_text, tags_json
                    FROM reviews
                    WHERE media_id = %s
                    ORDER BY review_id
                    """,
                    (str(media_id),),
                )
            rows = cursor.fetchall()
            results = []
            for row in rows:
                review = self._decode_review(row)
                if tag is None or tag in review.tags:
                    results.append((row["review_id"], review))
            return results
        finally:
            if cursor is not None:
                cursor.close()
            connection.close()

    def update_text(self, review_id, user_id, text):
        connection = self.connection_factory()
        cursor = None
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE reviews
                SET review_text = %s
                WHERE review_id = %s AND user_id = %s
                """,
                (text, review_id, user_id),
            )
            if cursor.rowcount != 1:
                raise RuntimeError("Review changed during update; please retry.")
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            if cursor is not None:
                cursor.close()
            connection.close()

    def delete(self, review_id, user_id):
        connection = self.connection_factory()
        cursor = None
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                DELETE FROM reviews
                WHERE review_id = %s AND user_id = %s
                """,
                (review_id, user_id),
            )
            if cursor.rowcount != 1:
                raise RuntimeError("Review changed during deletion; please retry.")
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            if cursor is not None:
                cursor.close()
            connection.close()
