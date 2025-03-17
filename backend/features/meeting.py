from fastapi import HTTPException
from pydantic import BaseModel
import sqlite3
import json
import uuid
from logger_config import setup_logger

# Set up logger
logger = setup_logger(__name__)


class MeetingCreate(BaseModel):
    participant_ids: list[str]
    userId: str = "SuperAdmin"


class MeetingTopic(BaseModel):
    meeting_id: str
    topic: str
    userId: str = "SuperAdmin"


async def create_meeting(meeting: MeetingCreate):
    """Create a meeting with a list of Participant IDs as participants."""
    logger.info("Creating new meeting with %d participants", len(meeting.participant_ids))

    conn = None
    try:
        conn = sqlite3.connect("roundtableai.db")
        cursor = conn.cursor()

        # Validate all participant IDs exist
        for participant_id in meeting.participant_ids:
            logger.debug("Validating participant ID: %s", participant_id)
            cursor.execute("SELECT id FROM participants WHERE id = ?", (participant_id,))
            if not cursor.fetchone():
                logger.error("Participant not found: %s", participant_id)
                raise HTTPException(status_code=404, detail=f"Participant ID '{participant_id}' not found")

        meeting_id = str(uuid.uuid4())
        participant_ids_json = json.dumps(meeting.participant_ids)

        logger.debug("Inserting meeting with ID: %s", meeting_id)
        cursor.execute("INSERT INTO meetings (id, participant_ids, topic, userId) VALUES (?, ?, ?, ?)", (meeting_id, participant_ids_json, None, meeting.userId))

        conn.commit()
        logger.info("Successfully created meeting: %s", meeting_id)
        return {"meeting_id": meeting_id}

    except sqlite3.Error as e:
        logger.error("Database error while creating meeting: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create meeting in database")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error while creating meeting: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while creating meeting")
    finally:
        if conn:
            conn.close()
            logger.debug("Database connection closed")


async def list_meetings():
    """List all meetings with participant details from SQLite."""
    logger.info("Fetching all meetings with participant details")

    conn = None
    try:
        conn = sqlite3.connect("roundtableai.db")
        cursor = conn.cursor()

        cursor.execute("SELECT id, participant_ids, topic, userId FROM meetings")
        meetings_raw = cursor.fetchall()
        logger.debug("Retrieved %d meetings from database", len(meetings_raw))

        meetings_data = []
        for row in meetings_raw:
            try:
                meeting = {"id": row[0], "participant_ids": json.loads(row[1]), "topic": row[2], "userId": row[3], "participants": []}

                # Fetch participant details for each participant_id
                for participant_id in meeting["participant_ids"]:
                    logger.debug("Fetching details for participant: %s in meeting: %s", participant_id, meeting["id"])
                    cursor.execute("SELECT id, name, role FROM participants WHERE id = ?", (participant_id,))
                    participant = cursor.fetchone()
                    if participant:
                        meeting["participants"].append({"participant_id": participant[0], "name": participant[1], "role": participant[2]})
                    else:
                        logger.warning("Participant %s not found for meeting %s", participant_id, meeting["id"])

                meetings_data.append(meeting)

            except json.JSONDecodeError as e:
                logger.error("Failed to parse participant_ids JSON for meeting %s: %s", row[0], str(e), exc_info=True)
                continue

        logger.info("Successfully retrieved %d meetings with participant details", len(meetings_data))
        return {"meetings": meetings_data}

    except sqlite3.Error as e:
        logger.error("Database error while fetching meetings: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve meetings from database")
    except Exception as e:
        logger.error("Unexpected error while fetching meetings: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while retrieving meetings")
    finally:
        if conn:
            conn.close()
            logger.debug("Database connection closed")


async def set_meeting_topic(meeting_topic: MeetingTopic):
    """Set a topic for an existing meeting."""
    logger.info("Setting topic for meeting: %s", meeting_topic.meeting_id)

    conn = None
    try:
        conn = sqlite3.connect("roundtableai.db")
        cursor = conn.cursor()

        # Check if meeting exists
        cursor.execute("SELECT id FROM meetings WHERE id = ?", (meeting_topic.meeting_id,))
        if not cursor.fetchone():
            logger.error("Meeting not found: %s", meeting_topic.meeting_id)
            raise HTTPException(status_code=404, detail=f"Meeting ID '{meeting_topic.meeting_id}' not found")

        # Update meeting topic
        cursor.execute("UPDATE meetings SET topic = ? WHERE id = ?", (meeting_topic.topic, meeting_topic.meeting_id))
        conn.commit()

        logger.info("Successfully set topic for meeting: %s", meeting_topic.meeting_id)
        return {"message": f"Topic '{meeting_topic.topic}' set for meeting '{meeting_topic.meeting_id}'"}

    except sqlite3.Error as e:
        logger.error("Database error while setting meeting topic: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update meeting topic in database")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error while setting meeting topic: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while setting meeting topic")
    finally:
        if conn:
            conn.close()
            logger.debug("Database connection closed")
