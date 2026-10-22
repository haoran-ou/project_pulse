import hashlib
import secrets
import time

from repositories.session_repository import insert_session, fetch_valid_session
from repositories.session_repository import insert_session

SESSION_LIFETIME_SECONDS = 60 * 60


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    token_hash = hash_session_token(token)
    expires_at = int(time.time()) + SESSION_LIFETIME_SECONDS

    insert_session(token_hash, user_id, expires_at)

    return token

def get_session_user_id(token: str) -> int | None:
    token_hash = hash_session_token(token)
    current_time = int(time.time())

    session = fetch_valid_session(token_hash, current_time)

    if session is None:
        return None

    return session["user_id"]