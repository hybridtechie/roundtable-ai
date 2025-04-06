from fastapi import HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict
from logger_config import setup_logger
from cosmos_db import cosmos_client

# Set up logger
logger = setup_logger(__name__)


class UserResponse(BaseModel):
    """Basic user information response model"""
    user_id: str
    display_name: str
    email: str


class UserDetailResponse(UserResponse):
    """Detailed user information response model with counts"""
    llm_providers_count: int = 0
    participants_count: int = 0
    meetings_count: int = 0
    groups_count: int = 0
    chat_sessions_count: int = 0


async def get_me(user_id: str) -> Dict:
    """Get basic user information"""
    try:
        logger.info("Fetching basic user information for user: %s", user_id)
        
        # Get user data from Cosmos DB
        user_data = await cosmos_client.get_user_data(user_id)
        if not user_data:
            logger.error("User not found with ID: %s", user_id)
            raise HTTPException(status_code=404, detail=f"User with ID '{user_id}' not found")
        
        # Extract basic user information
        response = {
            "user_id": user_data.get("id"),
            "display_name": user_data.get("display_name", ""),
            "email": user_data.get("email", "")
        }
        
        logger.info("Successfully retrieved basic user information for: %s", user_id)
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching user information for %s: %s", user_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while retrieving user information")


async def get_me_detail(user_id: str) -> Dict:
    """Get detailed user information with counts of various elements"""
    try:
        logger.info("Fetching detailed user information for user: %s", user_id)
        
        # Get user data from Cosmos DB
        user_data = await cosmos_client.get_user_data(user_id)
        if not user_data:
            logger.error("User not found with ID: %s", user_id)
            raise HTTPException(status_code=404, detail=f"User with ID '{user_id}' not found")
        
        # Extract basic user information
        response = {
            "user_id": user_data.get("id"),
            "display_name": user_data.get("display_name", ""),
            "email": user_data.get("email", ""),
            
            # Count various elements
            "llm_providers_count": len(user_data.get("llmAccounts", {}).get("providers", [])),
            "participants_count": len(user_data.get("participants", [])),
            "meetings_count": len(user_data.get("meetings", [])),
            "groups_count": len(user_data.get("groups", [])),
            
            # Count chat sessions (if available)
            "chat_sessions_count": len(user_data.get("chat_sessions", []))
        }
        
        logger.info("Successfully retrieved detailed user information for: %s", user_id)
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching detailed user information for %s: %s", user_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while retrieving detailed user information")