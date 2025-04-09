from pydantic import BaseModel, Field
from typing import List, Optional

# Attempt to import base models from feature files
# If these cause circular imports later, we might need to define base schemas here too.
try:
    from features.participant import ParticipantBase
except ImportError:
    # Define a fallback or raise an error if ParticipantBase is crucial here
    # For now, let's define a minimal placeholder if not found
    class ParticipantBase(BaseModel):
        name: str
        role: str
        context: Optional[str] = None
        user_id: Optional[str] = None  # Keep user_id optional here


try:
    from features.group import GroupBase
except ImportError:
    # Define a fallback or raise an error if GroupBase is crucial here
    class GroupBase(BaseModel):
        name: str
        description: Optional[str] = None
        user_id: Optional[str] = None  # Keep user_id optional here


# --- Generic Response Models ---
class DeleteResponse(BaseModel):
    """Standard response model for delete operations."""

    deleted_id: str


# --- Participant Response Models ---
class ParticipantResponse(ParticipantBase):
    """Response model for a single participant."""

    id: str
    # user_id: str # Consider if user_id should be exposed in responses


class ListParticipantsResponse(BaseModel):
    """Response model for listing multiple participants."""

    participants: List[ParticipantResponse]


# --- Group Response Models ---
class ParticipantInGroupResponse(BaseModel):
    """Response model for participant details within a group context."""

    id: str
    name: str
    role: str


class GroupResponse(GroupBase):
    """Response model for a single group, including its participants."""

    id: str
    participants: List[ParticipantInGroupResponse] = []
    context: Optional[str] = None  # Context might be specific to the group


class ListGroupsResponse(BaseModel):
    """Response model for listing multiple groups."""

    groups: List[GroupResponse]


# --- Meeting Response Models ---
class MeetingResponse(BaseModel):
    """Response model for a single meeting."""

    id: str
    group_id: str
    topic: Optional[str] = None
    status: str  # e.g., "scheduled", "in_progress", "completed"
    created_at: str  # Consider using datetime for better type handling if possible
    user_id: str  # ID of the user who owns/created the meeting


class ListMeetingsResponse(BaseModel):
    """Response model for listing multiple meetings."""

    meetings: List[MeetingResponse]


# --- User Response Models ---
class UserProfileResponse(BaseModel):
    """Response model for basic user profile information."""

    id: str  # Typically the user's email or unique identifier
    name: str
    email: str
    # Add other basic fields returned by get_me or login_user


class UserDetailResponse(UserProfileResponse):
    """Response model for detailed user information."""

    # Inherits from UserProfileResponse
    # Add additional fields returned by get_me_detail, e.g.:
    # llm_accounts: List[LLMAccountResponse] = [] # Example
    # groups: List[GroupResponse] = [] # Example
    # meetings: List[MeetingResponse] = [] # Example
    pass  # Add specific detailed fields here based on get_me_detail's return value


# --- LLM Account Response Models ---
class LLMAccountResponse(BaseModel):
    """Response model for a single LLM account configuration."""

    provider: str
    user_id: str
    is_default: bool
    # Add other relevant fields like API key placeholders if needed, but be careful with sensitive data


class ListLLMAccountsResponse(BaseModel):
    """Response model for listing multiple LLM account configurations."""

    accounts: List[LLMAccountResponse]


# --- Chat Session Response Models ---
class ChatSessionResponse(BaseModel):
    """Response model for a single chat session."""

    id: str
    meeting_id: str
    user_id: str
    created_at: str  # Consider using datetime
    # Add other fields returned by get_chat_session_by_id if any (e.g., last_message_timestamp)


class ListChatSessionsResponse(BaseModel):
    """Response model for listing multiple chat sessions."""

    chat_sessions: List[ChatSessionResponse]


# --- Question Generation Response ---
class QuestionsResponse(BaseModel):
    """Response model for the generated questions endpoint."""

    questions: List[str]
    topic: str
    group_id: str
    # user_id: str # User ID was passed to the function but might not be needed in response
