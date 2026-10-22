from repositories.user_repository import insert_user, fetch_user_by_username
from services.password_service import hash_password, verify_password

DUMMY_PASSWORD_HASH = hash_password("not-a-real-account-password")

def create_user_record(username: str, password: str) -> dict:
    password_hash = hash_password(password)

    return insert_user(
        username,
        password_hash,
    )

def authenticate_user(username: str, password: str) -> dict | None:
    user = fetch_user_by_username(username)

    if user is None:
        verify_password(password, DUMMY_PASSWORD_HASH)
        return None

    if not verify_password(password, user["password_hash"]):
        return None

    return {
        "id": user["id"],
        "username": user["username"],
    }