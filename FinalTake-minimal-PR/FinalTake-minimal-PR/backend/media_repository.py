from database import get_db_connection


class MediaRepository:
    FIELDS = """id, title, media_type, description, release_date,
                creator, image_url, created_at, updated_at"""

    @staticmethod
    def _query(sql, params=(), one=False):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(sql, params)
            return cursor.fetchone() if one else cursor.fetchall()
        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def list_media(media_type=None, limit=20, offset=0):
        sql = f"SELECT {MediaRepository.FIELDS} FROM media"
        params = []
        if media_type:
            sql += " WHERE media_type = %s"
            params.append(media_type)
        sql += " ORDER BY title ASC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        return MediaRepository._query(sql, tuple(params))

    @staticmethod
    def search_media(query, media_type=None, limit=20):
        sql = f"""SELECT {MediaRepository.FIELDS} FROM media
                  WHERE (title LIKE %s OR creator LIKE %s OR description LIKE %s)"""
        wildcard = f"%{query}%"
        params = [wildcard, wildcard, wildcard]
        if media_type:
            sql += " AND media_type = %s"
            params.append(media_type)
        sql += " ORDER BY title ASC LIMIT %s"
        params.append(limit)
        return MediaRepository._query(sql, tuple(params))

    @staticmethod
    def get_media(media_id):
        return MediaRepository._query(
            """SELECT m.id, m.title, m.media_type, m.description, m.release_date,
                      m.creator, m.image_url, m.created_at, m.updated_at,
                      ROUND(AVG(r.rating), 2) AS average_rating,
                      COUNT(r.id) AS review_count
               FROM media m LEFT JOIN reviews r ON r.media_id = m.id
               WHERE m.id = %s GROUP BY m.id""",
            (media_id,), one=True)

    @staticmethod
    def create_media(data, created_by=None):
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                """INSERT INTO media
                   (title, media_type, description, release_date, creator, image_url, created_by)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (data["title"], data["media_type"], data.get("description"),
                 data.get("release_date"), data.get("creator"), data.get("image_url"), created_by),
            )
            media_id = cursor.lastrowid
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()
        return MediaRepository.get_media(media_id)

    @staticmethod
    def get_reviews(media_id, limit=50):
        return MediaRepository._query(
            """SELECT r.id, r.rating, r.review_text, r.created_at,
                      u.id AS user_id, u.username
               FROM reviews r JOIN users u ON u.id = r.user_id
               WHERE r.media_id = %s ORDER BY r.created_at DESC LIMIT %s""",
            (media_id, limit))
