from fastapi import HTTPException
from pydantic import BaseModel
import sqlite3
import json
import uuid

class ChatroomCreate(BaseModel):
    agent_ids: list[str]

class ChatroomTopic(BaseModel):
    chatroom_id: str
    topic: str

async def create_chatroom(chatroom: ChatroomCreate):
    """Create a chatroom with a list of agent IDs as participants."""
    conn = sqlite3.connect("agents.db")
    cursor = conn.cursor()
    for agent_id in chatroom.agent_ids:
        cursor.execute("SELECT id FROM agents WHERE id = ?", (agent_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail=f"Agent ID '{agent_id}' not found")

    chatroom_id = str(uuid.uuid4())
    agent_ids_json = json.dumps(chatroom.agent_ids)
    cursor.execute("INSERT INTO chatrooms (id, agent_ids, topic) VALUES (?, ?, ?)", (chatroom_id, agent_ids_json, None))
    conn.commit()
    conn.close()
    return {"chatroom_id": chatroom_id}

async def list_chatrooms():
    """List all chatrooms from SQLite."""
    conn = sqlite3.connect("agents.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, agent_ids, topic FROM chatrooms")
    chatrooms_data = [{"id": row[0], "agent_ids": json.loads(row[1]), "topic": row[2]} for row in cursor.fetchall()]
    conn.close()
    return {"chatrooms": chatrooms_data}

async def set_chatroom_topic(chatroom_topic: ChatroomTopic):
    """Set a topic for an existing chatroom."""
    conn = sqlite3.connect("agents.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM chatrooms WHERE id = ?", (chatroom_topic.chatroom_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail=f"Chatroom ID '{chatroom_topic.chatroom_id}' not found")

    cursor.execute("UPDATE chatrooms SET topic = ? WHERE id = ?", (chatroom_topic.topic, chatroom_topic.chatroom_id))
    conn.commit()
    conn.close()
    return {"message": f"Topic '{chatroom_topic.topic}' set for chatroom '{chatroom_topic.chatroom_id}'"}