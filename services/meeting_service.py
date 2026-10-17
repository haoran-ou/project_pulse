from models import Meeting, MeetingUpdate
from repositories.meeting_repository import(
    insert_meeting,
    fetch_all_meetings,
    fetch_meeting_by_id,
    update_meeting,
    delete_meeting,
) 



def create_meeting_record(meeting: Meeting):
    return insert_meeting(
        meeting.project_name,
        meeting.meeting_text,
    )

def get_all_meetings(): 
    return fetch_all_meetings()

def get_meeting_by_id(meeting_id: int):
    return fetch_meeting_by_id(meeting_id)


def update_meeting_record(meeting_id: int, meeting_update: MeetingUpdate):

    return update_meeting(
        meeting_id,
        meeting_update.project_name,
        meeting_update.meeting_text,
    )

def delete_meeting_record(meeting_id: int):
    return delete_meeting(meeting_id)



