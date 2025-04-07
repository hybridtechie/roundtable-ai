from fastapi import HTTPException
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
import json
import uuid
from logger_config import setup_logger
from cosmos_db import cosmos_client


class ParticipantOrder(BaseModel):
    participant_id: str
    weight: int = Field(..., ge=0, le=10)
    order: int = Field(..., gt=0)

# Set up logger
logger = setup_logger(__name__)


class MeetingCreate(BaseModel):
    group_id: Optional[str] = None
    participant_id: Optional[str] = None
    strategy: str
    topic: str = "Default Topic"
    name: Optional[str] = None
    questions: List = []
    user_id: str = "roundtable_ai_admin"
    participant_order: Optional[List[ParticipantOrder]] = None
    _ts: Optional[float] = None

    @field_validator('group_id', 'participant_id')
    def validate_ids(cls, v, info):
        values = dict(info.data)
        if all(k in values for k in ['group_id', 'participant_id']):
            if values['group_id'] and values['participant_id']:
                raise ValueError("Cannot specify both group_id and participant_id")
            if not values['group_id'] and not values['participant_id']:
                raise ValueError("Must specify either group_id or participant_id")
        return v

    @field_validator('participant_order')
    def validate_participant_order(cls, v, info):
        if not v:
            return v
            
        # Check for duplicate orders
        orders = [p.order for p in v]
        if len(orders) != len(set(orders)):
            raise ValueError("Duplicate orders are not allowed")

        # If single participant, validate weight and order
        values = dict(info.data)
        if values.get('participant_id'):
            if len(v) != 1 or v[0].participant_id != values['participant_id']:
                raise ValueError("For single participant, participant_order must contain only that participant")
            if v[0].weight != 10 or v[0].order != 1:
                raise ValueError("Single participant must have weight=10 and order=1")
            
        return v


class Meeting(BaseModel):
    id: str
    participant_ids: List[str]
    participants: List[dict] = []
    group_ids: List[str] = []
    strategy: str
    topic: str = "Default Topic"
    name: Optional[str] = None
    questions: List = []
    user_id: str = "roundtable_ai_admin"
    participant_order: List[ParticipantOrder] = []
    _ts: Optional[float] = None


class MeetingTopic(BaseModel):
    meeting_id: str
    topic: str
    user_id: str = "roundtable_ai_admin"


async def create_meeting(meeting: MeetingCreate):
    """Create a meeting for a group or single participant with specified strategy and topic."""
    logger.info("Creating new meeting")

    try:
        participant_ids = []
        group_ids = []
        participant_order = []
        meeting_name = meeting.name

        if meeting.group_id:
            # Fetch group data to get participant_ids
            group = await cosmos_client.get_group(meeting.user_id, meeting.group_id)
            if not group:
                logger.error("Group not found: %s", meeting.group_id)
                raise HTTPException(status_code=404, detail=f"Group ID '{meeting.group_id}' not found")

            participant_ids = group.get('participant_ids', [])
            group_ids = [meeting.group_id]
            
            # Validate participant_order contains all group participants if provided
            if meeting.participant_order:
                order_participant_ids = {p.participant_id for p in meeting.participant_order}
                if order_participant_ids != set(participant_ids):
                    raise HTTPException(
                        status_code=400,
                        detail="participant_order must contain exactly the same participants as the group"
                    )
                participant_order = [
                    {"participant_id": p.participant_id, "weight": p.weight, "order": p.order}
                    for p in meeting.participant_order
                ]
            
            # Generate default name if not provided
            if not meeting_name:
                meeting_name = f"Meeting with {group.get('name', 'group')}"

        else:
            # Fetch participant data
            participant = await cosmos_client.get_participant(meeting.user_id, meeting.participant_id)
            if not participant:
                logger.error("Participant not found: %s", meeting.participant_id)
                raise HTTPException(status_code=404, detail=f"Participant ID '{meeting.participant_id}' not found")
            participant_ids = [meeting.participant_id]
            # For single participant, always set weight=10 and order=1
            participant_order = [{
                "participant_id": meeting.participant_id,
                "weight": 10,
                "order": 1
            }]

            
            # Generate default name if not provided
            if not meeting_name:
                meeting_name = f"Meeting with {participant.get('name', 'participant')}"

        meeting_id = str(uuid.uuid4())

        # Create meeting data
        # Add timestamp for meeting creation
        from time import time
        creation_ts = time()
        
        meeting_data = {
            "id": meeting_id,
            "participant_ids": participant_ids,
            "group_ids": group_ids,
            "user_id": meeting.user_id,
            "strategy": meeting.strategy,
            "topic": meeting.topic,
            "name": meeting_name,
            "questions": meeting.questions,
            "participant_order": participant_order,
            "_ts": creation_ts
        }

        await cosmos_client.add_meeting(meeting.user_id, meeting_data)
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
        
        # Sort meetings by _ts in descending order
        sorted_meetings = sorted(meetings, key=lambda x: x.get('_ts', 0), reverse=True)

        for meeting in sorted_meetings:
            meeting_data = {
                "id": meeting.get('id'),
                "strategy": meeting.get('strategy'),
                "participant_ids": meeting.get('participant_ids', []),
                "group_ids": meeting.get('group_ids', []),
                "topic": meeting.get('topic'),
                "name": meeting.get('name'),
                "user_id": meeting.get('user_id'),
                "participant_order": meeting.get('participant_order', []),
                "_ts": meeting.get('_ts'),
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

        # Convert participant_order dicts to ParticipantOrder objects
        participant_order = [
            ParticipantOrder(**order)
            for order in meeting_data.get('participant_order', [])
        ]

        meeting = Meeting(
            id=meeting_id,
            group_ids=meeting_data.get('group_ids', []),
            participant_ids=meeting_data.get('participant_ids', []),
            topic=meeting_data.get('topic', "Default Topic"),
            name=meeting_data.get('name'),
            user_id=meeting_data.get('user_id'),
            questions=meeting_data.get('questions', []),
            strategy=meeting_data.get('strategy', ""),
            participants=participant_details,
            participant_order=participant_order,
            _ts=meeting_data.get('_ts')
        )

        return meeting

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching meeting: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while fetching meeting")


async def delete_meeting(meeting_id: str, user_id: str):
    """Delete a meeting and its associated chat sessions."""
    logger.info("Deleting meeting: %s", meeting_id)

    try:
        # Check if meeting exists
        meeting_data = await cosmos_client.get_meeting(user_id, meeting_id)
        if not meeting_data:
            logger.error("Meeting not found: %s", meeting_id)
            raise HTTPException(status_code=404, detail=f"Meeting ID '{meeting_id}' not found")

        # Delete associated chat sessions
        chat_container = cosmos_client.client.get_database_client("roundtable").get_container_client("chat_sessions")
        query = f"SELECT * FROM c WHERE c.meeting_id = '{meeting_id}' AND c.user_id = '{user_id}'"
        chat_sessions = list(chat_container.query_items(
            query=query,
            partition_key=user_id
        ))
        
        # Delete each chat session
        for session in chat_sessions:
            chat_container.delete_item(
                item=session["id"],
                partition_key=user_id
            )
            logger.info(f"Deleted chat session {session['id']} for meeting {meeting_id}")
        
        # Delete the meeting
        await cosmos_client.delete_meeting(user_id, meeting_id)

        logger.info("Successfully deleted meeting and associated chat sessions: %s", meeting_id)
        return {"message": f"Meeting '{meeting_id}' and {len(chat_sessions)} associated chat sessions deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting meeting: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while deleting meeting")


async def set_meeting_topic(meeting_topic: MeetingTopic):
    """Set a topic for an existing meeting."""
    logger.info("Setting topic for meeting: %s", meeting_topic.meeting_id)

    try:
        # Check if meeting exists and get its data
        meeting_data = await cosmos_client.get_meeting(meeting_topic.user_id, meeting_topic.meeting_id)
        if not meeting_data:
            logger.error("Meeting not found: %s", meeting_topic.meeting_id)
            raise HTTPException(status_code=404, detail=f"Meeting ID '{meeting_topic.meeting_id}' not found")

        # Update meeting topic
        meeting_data['topic'] = meeting_topic.topic
        await cosmos_client.update_meeting(meeting_topic.user_id, meeting_topic.meeting_id, meeting_data)

        logger.info("Successfully set topic for meeting: %s", meeting_topic.meeting_id)
        return {"message": f"Topic '{meeting_topic.topic}' set for meeting '{meeting_topic.meeting_id}'"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error setting meeting topic: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while setting meeting topic")
