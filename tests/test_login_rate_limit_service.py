import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from services import login_rate_limit_service as limiter


class TestLoginRateLimitService(unittest.TestCase):
    def setUp(self):
        attempts = patch.object(limiter, "_attempts", {})
        attempts.start()
        self.addCleanup(attempts.stop)
        clock = patch.object(limiter.time, "monotonic", return_value=1000.0)
        self.clock = clock.start()
        self.addCleanup(clock.stop)

    def test_first_five_attempts_allowed_then_blocked(self):
        results = [limiter.allow_login_attempt("account:alice") for _ in range(7)]
        self.assertEqual(results, [True] * 5 + [False] * 2)
        self.assertEqual(limiter._attempts["account:alice"], (5, 1000.0))

    def test_keys_have_independent_budgets(self):
        for _ in range(5):
            self.assertTrue(limiter.allow_login_attempt("account:alice"))
        self.assertFalse(limiter.allow_login_attempt("account:alice"))
        self.assertTrue(limiter.allow_login_attempt("account:bob"))
        self.assertTrue(limiter.allow_login_attempt("ip:alice"))

    def test_window_expires_at_exact_boundary(self):
        for _ in range(5):
            limiter.allow_login_attempt("account:alice")
        self.clock.return_value = 1059.999
        self.assertFalse(limiter.allow_login_attempt("account:alice"))
        self.clock.return_value = 1060.0
        self.assertTrue(limiter.allow_login_attempt("account:alice"))
        self.assertEqual(limiter._attempts["account:alice"], (1, 1060.0))

    def test_attempt_does_not_extend_window(self):
        limiter.allow_login_attempt("account:alice")
        self.clock.return_value = 1030.0
        limiter.allow_login_attempt("account:alice")
        self.assertEqual(limiter._attempts["account:alice"], (2, 1000.0))

    def test_capacity_blocks_new_keys_until_expired_entries_are_removed(self):
        with patch.object(limiter, "MAX_TRACKED_KEYS", 2):
            self.assertTrue(limiter.allow_login_attempt("account:alice"))
            self.assertTrue(limiter.allow_login_attempt("account:bob"))
            self.assertFalse(limiter.allow_login_attempt("account:charlie"))
            self.assertTrue(limiter.allow_login_attempt("account:alice"))
            self.assertEqual(len(limiter._attempts), 2)
            self.clock.return_value = 1060.0
            self.assertTrue(limiter.allow_login_attempt("account:charlie"))
            self.assertEqual(limiter._attempts, {"account:charlie": (1, 1060.0)})

    def test_concurrent_attempts_do_not_exceed_limit(self):
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(
                limiter.allow_login_attempt, ["account:alice"] * 30
            ))
        self.assertEqual(sum(results), 5)
        self.assertEqual(limiter._attempts["account:alice"][0], 5)
