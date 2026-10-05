from database import get_db_connection


def insert_meeting(project_name: str, meeting_text: str) -> dict:
    connection = get_db_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO meetings(project_name, meeting_text)
            VALUES(?,?)
            """,
            (project_name,meeting_text),
        )
        connection.commit()
        meeting_id = cursor.lastrowid

    finally:
        connection.close()

    return{
        "id": meeting_id,
        "project_name": project_name,
        "meeting_text": meeting_text,
    }
        
def fetch_all_meetings() -> list[dict]:
    connection = get_db_connection()
    try:
        cursor = connection.execute(
            """
            SELECT id, project_name, meeting_text
            FROM meetings
            ORDER BY id
            """
        )
        meeting_rows = cursor.fetchall()
    finally:
        connection.close()
    meetings = []

    for meeting_row in meeting_rows:   
        meetings.append(dict(meeting_row))
    return meetings

def fetch_meeting_by_id(meeting_id: int) -> dict | None: #表示函数可能会返回两种结果。
    connection = get_db_connection()
    try:
        cursor = connection.execute(
            """
            SELECT id, project_name, meeting_text
            FROM meetings
            WHERE id = ?
            """,
            (meeting_id,),
        )
        meeting_record = cursor.fetchone()
    finally:
        connection.close()

    if meeting_record is None:
        return None
    
    return dict(meeting_record)

def update_meeting(
    meeting_id: int,
    project_name: str,
    meeting_text: str,
) -> dict | None:
    connection = get_db_connection()

    try:
        cursor = connection.execute(
        """
        UPDATE meetings
        SET project_name = ?, meeting_text = ?
        WHERE id = ?
        """,
        (project_name, meeting_text, meeting_id),
        )
        connection.commit()
        updated_count = cursor.rowcount

    finally:
        connection.close()

    if updated_count == 0:
        return None

    return {
        "id": meeting_id,
        "project_name": project_name,
        "meeting_text": meeting_text,
    }

def delete_meeting(meeting_id: int) -> dict | None:
    connection = get_db_connection()
    try:
        cursor = connection.execute(
            """
            SELECT id, project_name, meeting_text
            FROM meetings
            WHERE id = ?
            """,
            (meeting_id,),
        )
        meeting_record = cursor.fetchone()

        if meeting_record is None:
            return None

        deleted_meeting = dict(meeting_record)

        connection.execute(
            """
            DELETE FROM meetings
            WHERE id = ?
            """,
            (meeting_id,),
        )
        connection.commit()
    finally:
        connection.close()
    return deleted_meeting
        