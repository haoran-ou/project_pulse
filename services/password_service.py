from pwdlib import PasswordHash

ph = PasswordHash.recommended()

def hash_password(password: str) -> str:
    return ph.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    return ph.verify(password, hashed_password)