import os
import tempfile
import unittest

from models import Meeting, MeetingUpdate
from services.meeting_service import(
    create_meeting_record,
    get_meeting_by_id,
    get_all_meetings,
    update_meeting_record,
    delete_meeting_record,
)

from database import initialize_database

class TestMeetingService(unittest.TestCase):
    def setUp(self):
        self.original_directory = os.getcwd()
        self.temp_directory = tempfile.TemporaryDirectory()
        os.chdir(self.temp_directory.name)
        initialize_database()

    def tearDown(self):
        os.chdir(self.original_directory)
        self.temp_directory.cleanup()

    def test_create_meeting(self):
        meeting = Meeting(
            project_name = "Project Pulse",
            meeting_text = "Test meeting",
        )

        result = create_meeting_record(meeting)

        self.assertEqual(
            result,
            {
                "id": 1,
                "project_name": "Project Pulse",
                "meeting_text": "Test meeting",
            },
        )
        stored_meeting = get_meeting_by_id(result["id"])

        self.assertEqual(stored_meeting,result)

    def test_get_all_meetings(self):
        first_meeting = create_meeting_record(
            Meeting(
                project_name="Project Pulse",
                meeting_text="First meeting",
            )
        )
        second_meeting = create_meeting_record(
            Meeting(
                project_name="Project Pulse",
                meeting_text="Second meeting",
            )
        )

        result = get_all_meetings()

        self.assertEqual(result, [first_meeting, second_meeting])

    def test_get_missing_meeting_returns_none(self):
        result = get_meeting_by_id(999)
        self.assertIsNone(result)

    def test_update_meeting(self):
        created_meeting = create_meeting_record(
            Meeting(
                project_name="Project Pulse",
                meeting_text="Old notes",
            )
        )

        meeting_update = MeetingUpdate(
            meeting_text="Updated notes",
        )

        result = update_meeting_record(
            created_meeting["id"],
            meeting_update,
        )

        expected = {
            "id": 1,
            "project_name": "Project Pulse",
            "meeting_text": "Updated notes",
        }

        self.assertEqual(result, expected)

        stored_meeting = get_meeting_by_id(created_meeting["id"])
        self.assertEqual(stored_meeting, expected)

    def test_update_missing_meeting_returns_none(self):
        meeting_update = MeetingUpdate(
            meeting_text="Updated notes",
        )

        result = update_meeting_record(999, meeting_update)

        self.assertIsNone(result)

    def test_delete_meeting(self):
        created_meeting = create_meeting_record(
            Meeting(
                project_name="Project Pulse",
                meeting_text="Meeting to delete",
            )
        )

        deleted_meeting = delete_meeting_record(
            created_meeting["id"]
        )

        self.assertEqual(deleted_meeting, created_meeting)

        stored_meeting = get_meeting_by_id(created_meeting["id"])
        self.assertIsNone(stored_meeting)

    def test_delete_missing_meeting_returns_none(self):
        result = delete_meeting_record(999)

        self.assertIsNone(result)