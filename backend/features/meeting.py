from fastapi import HTTPException
from pydantic import BaseModel
import sqlite3
import json
import uuid

class MeetingCreate(BaseModel):
    aitwin_ids: list[str]
    userId: str = "SuperAdmin"

class MeetingTopic(BaseModel):
    meeting_id: str
    topic: str
    userId: str = "SuperAdmin"

async def create_meeting(meeting: MeetingCreate):
    """Create a meeting with a list of AiTwin IDs as participants."""
    conn = sqlite3.connect("aitwins.db")
    cursor = conn.cursor()
    for aitwin_id in meeting.aitwin_ids:
        cursor.execute("SELECT id FROM aitwins WHERE id = ?", (aitwin_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail=f"AiTwin ID '{aitwin_id}' not found")

    meeting_id = str(uuid.uuid4())
    aitwin_ids_json = json.dumps(meeting.aitwin_ids)
    cursor.execute(
        "INSERT INTO meetings (id, aitwin_ids, topic, userId) VALUES (?, ?, ?, ?)", 
        (meeting_id, aitwin_ids_json, None, meeting.userId)
    )
    conn.commit()
    conn.close()
    return {"meeting_id": meeting_id}

async def list_meetings():
    """List all meetings with participant details from SQLite."""
    conn = sqlite3.connect("aitwins.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, aitwin_ids, topic, userId FROM meetings")
    meetings_raw = cursor.fetchall()
    
    meetings_data = []
    for row in meetings_raw:
        meeting = {
            "id": row[0],
            "aitwin_ids": json.loads(row[1]),
            "topic": row[2],
            "userId": row[3],
            "participants": []
        }
        
        # Fetch participant details for each aitwin_id
        for aitwin_id in meeting["aitwin_ids"]:
            cursor.execute(
                "SELECT id, name, role FROM aitwins WHERE id = ?",
                (aitwin_id,)
            )
            aitwin = cursor.fetchone()
            if aitwin:
                meeting["participants"].append({
                    "aitwin_id": aitwin[0],
                    "name": aitwin[1],
                    "role": aitwin[2]
                })
        
        meetings_data.append(meeting)
    
    conn.close()
    return {"meetings": meetings_data}

async def set_meeting_topic(meeting_topic: MeetingTopic):
    """Set a topic for an existing meeting."""
    conn = sqlite3.connect("aitwins.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM meetings WHERE id = ?", (meeting_topic.meeting_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail=f"Meeting ID '{meeting_topic.meeting_id}' not found")

    cursor.execute(
        "UPDATE meetings SET topic = ? WHERE id = ?", 
        (meeting_topic.topic, meeting_topic.meeting_id)
    )
    conn.commit()
    conn.close()
    return {"message": f"Topic '{meeting_topic.topic}' set for meeting '{meeting_topic.meeting_id}'"}