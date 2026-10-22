import os
import sqlite3
import tempfile
import unittest

from database import get_db_connection, initialize_database


class TestUserSchema(unittest.TestCase):
    def setUp(self):
        original_directory = os.getcwd()
        temp_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temp_directory.cleanup)
        self.addCleanup(os.chdir, original_directory)
        os.chdir(temp_directory.name)
        initialize_database()

        self.connection = get_db_connection()
        self.addCleanup(self.connection.close)

    def test_reinitialization_preserves_user_and_meeting(self):
        # This placeholder exercises storage only, not password authentication.
        self.connection.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            ("alice", "test-only-hash-placeholder"),
        )
        self.connection.execute(
            "INSERT INTO meetings (project_name, meeting_text) VALUES (?, ?)",
            ("Existing project", "Existing notes"),
        )
        self.connection.commit()

        initialize_database()

        user = self.connection.execute("SELECT * FROM users").fetchone()
        self.assertEqual(user["id"], 1)
        self.assertEqual(user["username"], "alice")
        self.assertEqual(user["password_hash"], "test-only-hash-placeholder")
        self.assertIsNotNone(user["created_at"])
        meeting = self.connection.execute("SELECT * FROM meetings").fetchone()
        self.assertEqual(meeting["meeting_text"], "Existing notes")

    def test_duplicate_username_is_rejected(self):
        statement = "INSERT INTO users (username, password_hash) VALUES (?, ?)"
        self.connection.execute(statement, ("alice", "test-only-hash-placeholder"))

        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute(statement, ("alice", "another-placeholder"))

    def test_missing_password_hash_is_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute(
                "INSERT INTO users (username) VALUES (?)", ("alice",)
            )

    def test_user_can_have_multiple_persisted_sessions(self):
        user_id = self.connection.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            ("alice", "test-only-hash-placeholder"),
        ).lastrowid
        self.connection.executemany(
            "INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (?, ?, ?)",
            [("test-hash-one", user_id, 2000000000),
             ("test-hash-two", user_id, 2000000001)],
        )
        self.connection.commit()

        initialize_database()

        connection = get_db_connection()
        try:
            sessions = connection.execute(
                "SELECT * FROM sessions WHERE user_id = ? ORDER BY expires_at",
                (user_id,),
            ).fetchall()
        finally:
            connection.close()

        self.assertEqual(len(sessions), 2)
        self.assertEqual(sessions[0]["token_hash"], "test-hash-one")
        self.assertEqual(sessions[1]["token_hash"], "test-hash-two")
        self.assertEqual(sessions[0]["expires_at"], 2000000000)
        self.assertIsInstance(sessions[0]["created_at"], int)

    def test_session_for_missing_user_is_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute(
                "INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (?, ?, ?)",
                ("test-hash", 999, 2000000000),
            )

    def test_deleting_user_removes_only_their_sessions(self):
        self.connection.executemany(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            [("alice", "alice-placeholder"), ("bob", "bob-placeholder")],
        )
        self.connection.executemany(
            "INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (?, ?, ?)",
            [("alice-test-hash", 1, 2000000000),
             ("bob-test-hash", 2, 2000000000)],
        )
        self.connection.commit()

        self.connection.execute("DELETE FROM users WHERE id = ?", (1,))
        self.connection.commit()

        remaining = self.connection.execute("SELECT * FROM sessions").fetchall()
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0]["token_hash"], "bob-test-hash")
        self.assertEqual(remaining[0]["user_id"], 2)
