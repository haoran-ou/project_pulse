import time
from threading import Lock

WINDOW_SECONDS = 60
MAX_ATTEMPTS = 5
MAX_TRACKED_KEYS = 1000

_attempts: dict[str, tuple[int, float]] = {}
_lock = Lock()

def allow_login_attempt(key: str) -> bool:
    with _lock: #避免两个请求同时读到次数为 4，然后都获准进入。离开这个代码块时，锁会自动释放，包括执行 return 时。
        now = time.monotonic()

        expired_keys = [
            stored_key
            for stored_key, (_, started_at) in _attempts.items()
            if now - started_at >= WINDOW_SECONDS
        ]
        for expired_key in expired_keys:
            del _attempts[expired_key]

        if key not in _attempts:
            if len(_attempts) >= MAX_TRACKED_KEYS:
                return False

            _attempts[key] = (1, now)
            return True

        count, started_at = _attempts[key]

        if count >= MAX_ATTEMPTS:
            return False

        _attempts[key] = (count + 1, started_at)
        return True