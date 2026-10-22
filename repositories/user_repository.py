from database import get_db_connection


def fetch_user_by_username(username: str) -> dict | None:
    connection = get_db_connection()

    try:
        cursor = connection.execute(
            """
            SELECT id, username, password_hash, created_at
            FROM users
            WHERE username = ?
            """,
            (username,),
        )
        user_record = cursor.fetchone()
    finally:
        connection.close()

    if user_record is None:
        return None

    return dict(user_record)

def insert_user(username: str, password_hash: str) -> dict:
    connection = get_db_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO users (username, password_hash)
            VALUES (?, ?)
            """,
            (username, password_hash),
        )
        user_id = cursor.lastrowid
        connection.commit()
    finally:
        connection.close()

    return {
        "id": user_id,
        "username": username,
    }