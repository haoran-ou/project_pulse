import json

from database import get_db_connection

def insert_analysis(
    meeting_id: int,
    meeting_text_snapshot: str,
    analysis:dict,
) -> dict:
    tasks_json = json.dumps(analysis["tasks"], ensure_ascii=False)
    risks_json = json.dumps(analysis["risks"], ensure_ascii=False)

    connection = get_db_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO meeting_analyses (
                meeting_id,
                meeting_text_snapshot,
                summary,
                tasks_json,
                risks_json
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                meeting_id,
                meeting_text_snapshot,
                analysis["summary"],
                tasks_json,
                risks_json,
            ),
        )
        analysis_id = cursor.lastrowid

        analysis_row = connection.execute(
            """
            SELECT id, meeting_id, meeting_text_snapshot,
                   summary, tasks_json, risks_json, created_at
            FROM meeting_analyses
            WHERE id = ?
            """,
            (analysis_id,),
        ).fetchone()

        connection.commit()

    finally:
        connection.close()

    return {
        "id": analysis_row["id"],
        "meeting_id": analysis_row["meeting_id"],
        "meeting_text_snapshot": analysis_row["meeting_text_snapshot"],
        "summary": analysis_row["summary"],
        "tasks": json.loads(analysis_row["tasks_json"]),
        "risks": json.loads(analysis_row["risks_json"]),
        "created_at": analysis_row["created_at"],
        }

def fetch_analyses_by_meeting_id(meeting_id: int) -> list[dict]:
    connection = get_db_connection()

    try:
        analysis_rows = connection.execute(
            """
            SELECT id, meeting_id, meeting_text_snapshot,
            summary, tasks_json, risks_json, created_at
            FROM meeting_analyses
            WHERE meeting_id = ?
            ORDER BY id DESC
            """,
            (meeting_id,),
        ).fetchall()

    finally:
        connection.close()

    analyses = []

    for analysis_row in analysis_rows:
        analyses.append({
            "id": analysis_row["id"],
            "meeting_id": analysis_row["meeting_id"],
            "meeting_text_snapshot": analysis_row["meeting_text_snapshot"],
            "summary": analysis_row["summary"],
            "tasks": json.loads(analysis_row["tasks_json"]),
            "risks": json.loads(analysis_row["risks_json"]),
            "created_at": analysis_row["created_at"],
        })

    return analyses
