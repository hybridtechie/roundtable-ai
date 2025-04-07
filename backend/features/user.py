from fastapi import HTTPException, Header
from pydantic import BaseModel, Field
from typing import Optional, Dict
from logger_config import setup_logger
from dotenv import load_dotenv
import os
from jose import jwt
from fastapi import Depends
from cosmos_db import cosmos_client
import copy
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
# Load environment variables
load_dotenv()

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE")

async def validate_id_token(id_token: str) -> Dict:
    """Validate the idToken from Auth0 and extract claims"""
    try:
        # Fetch the public key from Auth0
        jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
        jwks_client = jwt.JWT()
        jwks = jwks_client.get_unverified_headers(id_token)
        
        # Decode the token
        payload = jwt.decode(
            id_token,
            jwks,
            algorithms=['RS256'],
            audience=AUTH0_AUDIENCE,
            issuer=f"https://{AUTH0_DOMAIN}/"
        )
        
        return payload
    except jwt.JWTError as e:
        logger.error("Token validation error: %s", str(e))
        raise HTTPException(status_code=401, detail="Invalid token")

async def extract_email_from_token(id_token: str) -> str:
    """Extract the email claim from the idToken"""
    payload = await validate_id_token(id_token)
    email = payload.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email claim not found in token")
    return email

    chat_sessions_count: int = 0

async def login_user(authorization: str = Header(...)) -> Dict:
    """Handle user login with idToken validation and user creation/retrieval"""
    try:
        # Extract token from Authorization header
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        id_token = authorization.split(" ")[1]

        # Validate token and extract email
        payload = await validate_id_token(id_token)
        email = payload.get("email")
        name = payload.get("name")
        if not email:
            raise HTTPException(status_code=400, detail="Email claim not found in token")

        # Check if user exists in Cosmos DB
        user_data = await cosmos_client.get_user_by_email(email)
        
        if not user_data:
            # Fetch admin template
            admin_template = await cosmos_client.get_user_data("roundtable_ai_admin")
            if not admin_template:
                raise HTTPException(status_code=500, detail="Admin template not found")
            
            # Clone admin template and update user-specific fields
            new_user = copy.deepcopy(admin_template)
            new_user["id"] = email
            new_user["email"] = email
            new_user["display_name"] = name
            
            # Create new user in Cosmos DB
            await cosmos_client.create_user(new_user)
            return await get_me(email)
        
        return await get_me(email)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Login error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during login")


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
        response = {"user_id": user_data.get("id"), "display_name": user_data.get("display_name", ""), "email": user_data.get("email", "")}

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
            "chat_sessions_count": len(user_data.get("chat_sessions", [])),
        }

        logger.info("Successfully retrieved detailed user information for: %s", user_id)
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching detailed user information for %s: %s", user_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while retrieving detailed user information")
