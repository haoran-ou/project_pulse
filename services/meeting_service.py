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
    meeting_record = fetch_meeting_by_id(meeting_id)
    
    if meeting_record is None:
        return None
    
    update_project_name = meeting_record["project_name"]
    update_meeting_text = meeting_record["meeting_text"]

    if meeting_update.project_name is not None:
        update_project_name = meeting_update.project_name
    
    if meeting_update.meeting_text is not None:
        update_meeting_text = meeting_update.meeting_text

    return update_meeting(
        meeting_id,
        update_project_name,
        update_meeting_text
    )

def delete_meeting_record(meeting_id: int):
    return delete_meeting(meeting_id)



