from fastapi import APIRouter, HTTPException
from models import Meeting, MeetingUpdate
from services.meeting_service import (
    create_meeting_record,
    delete_meeting_record,
    get_all_meetings,
    get_meeting_by_id,
    update_meeting_record,
)
from services.analysis_service import analyze_meeting as analyze_meeting_service

from services.analysis_service import(
    get_meeting_analyses_history,
    analyze_and_save_meeting,
) 



router = APIRouter()

@router.post("/meeting/analyze", tags=["Analysis"])
def analyze_meeting(meeting: Meeting):
    analysis = analyze_meeting_service(meeting.meeting_text)

    return {
        "message": "Meeting analyzed successfully",
        "project_name": meeting.project_name,
        "summary": analysis["summary"],
        "tasks": analysis["tasks"],
        "task_count": len(analysis["tasks"]),
        "risks": analysis["risks"],
        "risk_count": len(analysis["risks"]),
    }

@router.post("/meetings", tags=["Meetings"], status_code=201)
def create_meeting(meeting: Meeting):
    return create_meeting_record(meeting)

@router.get("/meetings", tags=["Meetings"])
def get_meetings():
    return get_all_meetings()


@router.get("/meetings/{meeting_id}", tags=["Meetings"]) #查询某一条会议
def get_meeting(meeting_id: int):
    meeting = get_meeting_by_id(meeting_id)
    if meeting is None:
        raise HTTPException( #括号不能另起一行一个
            status_code = 404,
            detail = "Meeting not found"
        )
    return meeting

@router.patch("/meetings/{meeting_id}", tags=["Meetings"])
def update_meeting(meeting_id: int, meeting_update: MeetingUpdate):
    updated_meeting = update_meeting_record(meeting_id, meeting_update)
    if updated_meeting is None:
        raise HTTPException(
            status_code = 404,
            detail = "Meeting not found",
        )

    return updated_meeting


@router.delete("/meetings/{meeting_id}", tags=["Meetings"])
def delete_meeting(meeting_id: int):
    deleted_meeting = delete_meeting_record(meeting_id)

    if deleted_meeting is None:
        raise HTTPException(
            status_code = 404,
            detail = "Meeting not found",
        )

    return {
        "message": "Meeting deleted successfully",
        "meeting": deleted_meeting
    }


@router.get("/meetings/{meeting_id}/analyses", tags=["Analysis"])
def get_meeting_analysis_history(meeting_id: int):

    history = get_meeting_analyses_history(meeting_id)

    if history is None:
        raise HTTPException(
            status_code = 404,
            detail = "Meeting not found",
        )
    return history

@router.post("/meetings/{meeting_id}/analyses", tags=["Analysis"], status_code = 201,)
def create_meeting_analysis(meeting_id: int):
    analysis = analyze_and_save_meeting(meeting_id)

    if analysis is None:
        raise HTTPException(
            status_code = 404,
            detail = "Meeting not found",
        )
    return analysis