from fastapi import FastAPI, HTTPException
from models import Meeting, MeetingUpdate


app = FastAPI(
    title="Project Pulse API",
    description="A backend API for meeting and project management.",
    version="0.1.0",
)

# Temporary in-memory storage.
# Data resets when the application restarts.
meeting_history = []
next_meeting_id = 1


def fake_analyze_meeting(meeting_text: str) -> dict:
    risks = []

    if "risk" in meeting_text.lower():
        risks.append("A potential project risk was detected.")

    analysis = {
        "summary": f"Basic analysis of the meeting: {meeting_text}",
        "tasks": [
            {
                "task": "Review the meeting notes",
                "owner": "Unassigned",
                "status": "Pending",
            }
        ],
        "risks": risks,
    }

    return analysis


@app.post("/meeting/analyze", tags=["Analysis"])
def analyze_meeting(meeting: Meeting):
    analysis = fake_analyze_meeting(meeting.meeting_text)

    return {
        "message": "Meeting analyzed successfully",
        "project_name": meeting.project_name,
        "summary": analysis["summary"],
        "tasks": analysis["tasks"],
        "task_count": len(analysis["tasks"]),
        "risks": analysis["risks"],
        "risk_count": len(analysis["risks"]),
    }


@app.post("/meetings", tags=["Meetings"], status_code=201)
def create_meeting(meeting: Meeting):
    global next_meeting_id

    meeting_record = {
        "id": next_meeting_id,
        "project_name": meeting.project_name,
        "meeting_text": meeting.meeting_text,
    }

    meeting_history.append(meeting_record)
    next_meeting_id += 1

    return meeting_record


@app.get("/meetings", tags=["Meetings"])
def get_meetings():
    return meeting_history


@app.get("/meetings/{meeting_id}", tags=["Meetings"])
def get_meeting(meeting_id: int):
    for meeting_record in meeting_history:
        if meeting_record["id"] == meeting_id:
            return meeting_record

    raise HTTPException(
        status_code=404,
        detail="Meeting not found",
    )


@app.patch("/meetings/{meeting_id}", tags=["Meetings"])
def update_meeting(meeting_id: int, meeting_update: MeetingUpdate):
    for meeting_record in meeting_history:
        if meeting_record["id"] == meeting_id:
            if meeting_update.project_name is not None:
                meeting_record["project_name"] = meeting_update.project_name

            if meeting_update.meeting_text is not None:
                meeting_record["meeting_text"] = meeting_update.meeting_text

            return meeting_record

    raise HTTPException(
        status_code=404,
        detail="Meeting not found",
    )


@app.delete("/meetings/{meeting_id}", tags=["Meetings"])
def delete_meeting(meeting_id: int):
    for index, meeting_record in enumerate(meeting_history):
        if meeting_record["id"] == meeting_id:
            deleted_meeting = meeting_history.pop(index)

            return {
                "message": "Meeting deleted successfully",
                "meeting": deleted_meeting,
            }

    raise HTTPException(
        status_code=404,
        detail="Meeting not found",
    )
