import unittest
from unittest.mock import patch

from models import Meeting
from routers.meetings import analyze_meeting as analyze_meeting_route

class TestMeetingRouter(unittest.TestCase):
    @patch("routers.meetings.analyze_meeting_service")
    def test_analysis_meeting_route(self, mock_analyze_meeting):
        mock_analyze_meeting.return_value = {
            "summary": "Mock meeting summary.",
            "tasks": [
                {
                    "task": "Add API tests",
                    "owner": "Bob",
                    "status": "Pending",
                }
            ],
            "risks": ["Limited Azure quota may delay deployment."],
        }

        meeting = Meeting(
            project_name="Router Test",
            meeting_text="The deadline has a risk.",
        )

        response = analyze_meeting_route(meeting)

        self.assertEqual(response["project_name"], "Router Test")
        self.assertEqual(response["task_count"], 1)
        self.assertEqual(response["risk_count"], 1)
