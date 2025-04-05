from fastapi import HTTPException
from pydantic import BaseModel, validator
from typing import Optional
import json
import uuid
from logger_config import setup_logger
from cosmos_db import cosmos_client

# Set up logger
logger = setup_logger(__name__)


class MeetingCreate(BaseModel):
    group_id: Optional[str] = None
    participant_id: Optional[str] = None
    strategy: str
    topic: str = "Default Topic"
    name: Optional[str] = None
    questions: list = []
    userId: str = "SuperAdmin"

    @validator('group_id', 'participant_id')
    def validate_ids(cls, v, values):
        if 'group_id' in values and 'participant_id' in values:
            if values['group_id'] and values['participant_id']:
                raise ValueError("Cannot specify both group_id and participant_id")
            if not values['group_id'] and not values['participant_id']:
                raise ValueError("Must specify either group_id or participant_id")
        return v


class Meeting(BaseModel):
    id: str
    participant_ids: list
    participants: list = []
    group_ids: list = []
    strategy: str
    topic: str = "Default Topic"
    name: Optional[str] = None
    questions: list = []
    userId: str = "SuperAdmin"


class MeetingTopic(BaseModel):
    meeting_id: str
    topic: str
    userId: str = "SuperAdmin"


async def create_meeting(meeting: MeetingCreate):
    """Create a meeting for a group or single participant with specified strategy and topic."""
    logger.info("Creating new meeting")

    try:
        participant_ids = []
        group_ids = []
        meeting_name = meeting.name

        if meeting.group_id:
            # Fetch group data to get participant_ids
            group = await cosmos_client.get_group(meeting.userId, meeting.group_id)
            if not group:
                logger.error("Group not found: %s", meeting.group_id)
                raise HTTPException(status_code=404, detail=f"Group ID '{meeting.group_id}' not found")

            participant_ids = group.get('participant_ids', [])
            group_ids = [meeting.group_id]
            
            # Generate default name if not provided
            if not meeting_name:
                meeting_name = f"Meeting with {group.get('name', 'group')}"

        else:
            # Fetch participant data
            participant = await cosmos_client.get_participant(meeting.userId, meeting.participant_id)
            if not participant:
                logger.error("Participant not found: %s", meeting.participant_id)
                raise HTTPException(status_code=404, detail=f"Participant ID '{meeting.participant_id}' not found")

            participant_ids = [meeting.participant_id]
            
            # Generate default name if not provided
            if not meeting_name:
                meeting_name = f"Meeting with {participant.get('name', 'participant')}"

        meeting_id = str(uuid.uuid4())

        # Create meeting data
        meeting_data = {
            "id": meeting_id,
            "participant_ids": participant_ids,
            "group_ids": group_ids,
            "userId": meeting.userId,
            "strategy": meeting.strategy,
            "topic": meeting.topic,
            "name": meeting_name,
            "questions": meeting.questions
        }

        await cosmos_client.add_meeting(meeting.userId, meeting_data)
        logger.info("Successfully created meeting: %s", meeting_id)
        return {"meeting_id": meeting_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating meeting: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while creating meeting")


async def list_meetings(user_id: str):
    """List all meetings with participant details."""
    logger.info("Fetching all meetings with participant details")

    try:
        meetings = await cosmos_client.list_meetings(user_id)
        meetings_data = []

        for meeting in meetings:
            meeting_data = {
                "id": meeting.get('id'),
                "participant_ids": meeting.get('participant_ids', []),
                "topic": meeting.get('topic'),
                "name": meeting.get('name'),
                "userId": meeting.get('userId'),
                "participants": []
            }

            # Fetch participant details
            for participant_id in meeting_data["participant_ids"]:
                participant = await cosmos_client.get_participant(user_id, participant_id)
                if participant:
                    meeting_data["participants"].append({
                        "id": participant.get('id'),
                        "name": participant.get('name'),
                        "role": participant.get('role'),
                        "persona_description": participant.get('persona_description')
                    })
                else:
                    logger.warning("Participant %s not found for meeting %s", participant_id, meeting_data["id"])

            meetings_data.append(meeting_data)

        logger.info("Successfully retrieved %d meetings with participant details", len(meetings_data))
        return {"meetings": meetings_data}

    except Exception as e:
        logger.error("Error listing meetings: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while retrieving meetings")


async def get_meeting(meeting_id: str, user_id: str) -> Meeting:
    """Get a meeting by ID with participant details."""
    logger.info("Fetching meeting: %s", meeting_id)

    try:
        meeting_data = await cosmos_client.get_meeting(user_id, meeting_id)
        if not meeting_data:
            logger.error("Meeting not found: %s", meeting_id)
            raise HTTPException(status_code=404, detail=f"Meeting ID '{meeting_id}' not found")

        participant_details = []
        for participant_id in meeting_data.get('participant_ids', []):
            participant = await cosmos_client.get_participant(user_id, participant_id)
            if participant:
                participant_details.append({
                    "participant_id": participant.get('id'),
                    "name": participant.get('name'),
                    "role": participant.get('role'),
                    "persona_description": participant.get('persona_description')
                })
            else:
                logger.warning("Participant %s not found for meeting %s", participant_id, meeting_id)

        meeting = Meeting(
            id=meeting_id,
            group_ids=meeting_data.get('group_ids', []),
            participant_ids=meeting_data.get('participant_ids', []),
            topic=meeting_data.get('topic', "Default Topic"),
            name=meeting_data.get('name'),
            userId=meeting_data.get('userId'),
            questions=meeting_data.get('questions', []),
            strategy=meeting_data.get('strategy', ""),
            participants=participant_details
        )

        return meeting

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching meeting: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while fetching meeting")


async def set_meeting_topic(meeting_topic: MeetingTopic):
    """Set a topic for an existing meeting."""
    logger.info("Setting topic for meeting: %s", meeting_topic.meeting_id)

    try:
        # Check if meeting exists and get its data
        meeting_data = await cosmos_client.get_meeting(meeting_topic.userId, meeting_topic.meeting_id)
        if not meeting_data:
            logger.error("Meeting not found: %s", meeting_topic.meeting_id)
            raise HTTPException(status_code=404, detail=f"Meeting ID '{meeting_topic.meeting_id}' not found")

        # Update meeting topic
        meeting_data['topic'] = meeting_topic.topic
        await cosmos_client.update_meeting(meeting_topic.userId, meeting_topic.meeting_id, meeting_data)

        logger.info("Successfully set topic for meeting: %s", meeting_topic.meeting_id)
        return {"message": f"Topic '{meeting_topic.topic}' set for meeting '{meeting_topic.meeting_id}'"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error setting meeting topic: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while setting meeting topic")
