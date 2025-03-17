from fastapi import HTTPException
from pydantic import BaseModel
import sqlite3
import json
import uuid


class MeetingCreate(BaseModel):
    participant_ids: list[str]
    userId: str = "SuperAdmin"


class MeetingTopic(BaseModel):
    meeting_id: str
    topic: str
    userId: str = "SuperAdmin"


async def create_meeting(meeting: MeetingCreate):
    """Create a meeting with a list of Participant IDs as participants."""
    conn = sqlite3.connect("roundtableai.db")
    cursor = conn.cursor()
    for participant_id in meeting.participant_ids:
        cursor.execute("SELECT id FROM participants WHERE id = ?", (participant_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail=f"Participant ID '{participant_id}' not found")

    meeting_id = str(uuid.uuid4())
    participant_ids_json = json.dumps(meeting.participant_ids)
    cursor.execute("INSERT INTO meetings (id, participant_ids, topic, userId) VALUES (?, ?, ?, ?)", (meeting_id, participant_ids_json, None, meeting.userId))
    conn.commit()
    conn.close()
    return {"meeting_id": meeting_id}


async def list_meetings():
    """List all meetings with participant details from SQLite."""
    conn = sqlite3.connect("roundtableai.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, participant_ids, topic, userId FROM meetings")
    meetings_raw = cursor.fetchall()

    meetings_data = []
    for row in meetings_raw:
        meeting = {"id": row[0], "participant_ids": json.loads(row[1]), "topic": row[2], "userId": row[3], "participants": []}

        # Fetch participant details for each participant_id
        for participant_id in meeting["participant_ids"]:
            cursor.execute("SELECT id, name, role FROM participants WHERE id = ?", (participant_id,))
            participant = cursor.fetchone()
            if participant:
                meeting["participants"].append({"participant_id": participant[0], "name": participant[1], "role": participant[2]})

        meetings_data.append(meeting)

    conn.close()
    return {"meetings": meetings_data}


async def set_meeting_topic(meeting_topic: MeetingTopic):
    """Set a topic for an existing meeting."""
    conn = sqlite3.connect("roundtableai.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM meetings WHERE id = ?", (meeting_topic.meeting_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail=f"Meeting ID '{meeting_topic.meeting_id}' not found")

    cursor.execute("UPDATE meetings SET topic = ? WHERE id = ?", (meeting_topic.topic, meeting_topic.meeting_id))
    conn.commit()
    conn.close()
    return {"message": f"Topic '{meeting_topic.topic}' set for meeting '{meeting_topic.meeting_id}'"}
