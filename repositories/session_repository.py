from database import get_db_connection

def insert_session(
    token_hash: str,
    user_id: int,
    expires_at: int,
) -> None:
    connection = get_db_connection()

    try:
        connection.execute(
            """
            INSERT INTO sessions (token_hash, user_id, expires_at)
            VALUES (?, ?, ?)
            """,
            (token_hash, user_id, expires_at),
        )
        connection.commit()
    finally:
        connection.close()

def fetch_valid_session(
    token_hash: str,
    current_time: int,
) -> dict | None:
    connection = get_db_connection()

    try:
        cursor = connection.execute(
            """
            SELECT token_hash, user_id, created_at, expires_at
            FROM sessions
            WHERE token_hash = ? AND expires_at > ?
            """,
            (token_hash, current_time),
        )
        session = cursor.fetchone()
    finally:
        connection.close()

    if session is None:
        return None

    return dict(session)

def delete_session(token_hash: str) -> None:
    connection = get_db_connection()

    try:
        connection.execute(
            """
            DELETE FROM sessions
            WHERE token_hash = ?
            """,
            (token_hash,),
        )
        connection.commit()
    finally:
        connection.close()