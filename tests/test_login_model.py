import unittest

from pydantic import SecretStr, ValidationError

from models import LoginRequest


class TestLoginRequest(unittest.TestCase):
    def test_valid_input_preserves_the_secret_for_verification(self):
        data = LoginRequest(username="alice", password="test-only-password")

        self.assertEqual(data.username, "alice")
        self.assertIsInstance(data.password, SecretStr)
        self.assertEqual(data.password.get_secret_value(), "test-only-password")

    def test_default_display_and_json_mask_the_password(self):
        data = LoginRequest(username="alice", password="test-only-password")

        self.assertNotIn("test-only-password", repr(data))
        self.assertNotIn("test-only-password", data.model_dump_json())
        self.assertEqual(data.model_dump(mode="json")["password"], "**********")

    def test_length_boundaries_are_accepted(self):
        for username, password in (("a", "p"), ("u" * 64, "p" * 1024)):
            with self.subTest(username_length=len(username), password_length=len(password)):
                data = LoginRequest(username=username, password=password)
                self.assertEqual(data.password.get_secret_value(), password)

    def test_missing_empty_overlong_and_invalid_types_are_rejected(self):
        invalid_inputs = [
            {},
            {"username": "alice"},
            {"password": "test-only-password"},
            {"username": "", "password": "test-only-password"},
            {"username": "alice", "password": ""},
            {"username": "u" * 65, "password": "test-only-password"},
            {"username": "alice", "password": "p" * 1025},
            {"username": None, "password": "test-only-password"},
            {"username": "alice", "password": None},
            {"username": 123, "password": "test-only-password"},
            {"username": "alice", "password": 123},
        ]
        for index, values in enumerate(invalid_inputs):
            with self.subTest(case=index):
                with self.assertRaises(ValidationError):
                    LoginRequest(**values)
