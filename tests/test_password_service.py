import unittest

from services.password_service import hash_password, verify_password


class TestPasswordService(unittest.TestCase):
    def test_correct_password_matches_hash(self):
        password = "test-only-password"
        stored_hash = hash_password(password)

        self.assertIsInstance(stored_hash, str)
        self.assertNotEqual(stored_hash, password)
        self.assertTrue(verify_password(password, stored_hash))

    def test_wrong_password_is_rejected(self):
        stored_hash = hash_password("test-only-password")

        self.assertFalse(verify_password("wrong-password", stored_hash))

    def test_same_password_produces_distinct_valid_hashes(self):
        password = "test-only-password"
        first_hash = hash_password(password)
        second_hash = hash_password(password)

        self.assertNotEqual(first_hash, second_hash)
        self.assertTrue(verify_password(password, first_hash))
        self.assertTrue(verify_password(password, second_hash))
