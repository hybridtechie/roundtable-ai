from fastapi import HTTPException, Header
from pydantic import BaseModel, Field
from typing import Optional, Dict
from logger_config import setup_logger
from dotenv import load_dotenv
import os
from jose import jwt
from jose.exceptions import JWTError
from fastapi import Depends
import requests
import json
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
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE")  # Keep for potential future use with access tokens
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")  # Add Client ID for ID token validation


def fetch_jwks() -> Dict:
    """Fetch the JWKS from Auth0"""
    try:
        jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
        response = requests.get(jwks_url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error("Error fetching JWKS: %s", str(e))
        raise HTTPException(status_code=500, detail="Error fetching JWKS from Auth0")


def get_key_from_jwks(jwks: Dict, kid: str) -> Dict:
    """Get the correct key from JWKS using the key ID"""
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key
    raise HTTPException(status_code=401, detail="Invalid token: Key ID not found in JWKS")


async def validate_id_token(id_token: str) -> Dict:
    """
    Validate the ID token from Auth0 and extract claims.

    This function verifies:
    1. Token signature using Auth0's JWKS
    2. Token audience matches our client ID
    3. Token issuer is our Auth0 domain
    4. Token expiration and issuance time
    """
    if not AUTH0_DOMAIN or not AUTH0_CLIENT_ID:
        logger.error("Auth0 domain or client ID not configured in environment variables.")
        raise HTTPException(status_code=500, detail="Authentication service not configured")

    try:
        # Get the unverified headers to extract the key ID (kid)
        headers = jwt.get_unverified_headers(id_token)
        kid = headers.get("kid")
        if not kid:
            logger.warning("Token header missing 'kid'")
            raise HTTPException(status_code=401, detail="Invalid token: No key ID in header")

        # Fetch JWKS and find the key corresponding to the kid
        jwks = fetch_jwks()
        key = get_key_from_jwks(jwks, kid)  # This function already raises HTTPException if key not found

        # Decode and validate the token using the public key from JWKS
        # Note: python-jose requires the key in JWK format
        payload = jwt.decode(
            id_token,
            key=key,
            algorithms=["RS256"],  # Standard algorithm for Auth0 RS256 signed tokens
            audience=AUTH0_CLIENT_ID,  # Use Client ID for ID token audience validation
            issuer=f"https://{AUTH0_DOMAIN}/",  # Validate the issuer
            # Standard claims like exp, iat, iss, aud are verified by default by python-jose
        )

        logger.info("ID token validated successfully for issuer: %s", payload.get("iss"))
        return payload
    except JWTError as e:
        logger.error("ID Token validation failed: %s", str(e))
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    except HTTPException as e:  # Re-raise HTTPExceptions from helpers
        raise e
    except Exception as e:  # Catch other potential errors during validation
        logger.error("An unexpected error occurred during token validation: %s", str(e))
        raise HTTPException(status_code=500, detail="Token validation error")


# Removed extract_email_from_token as login_user handles payload directly
# Removed unused chat_sessions_count variable
async def login_user(name: str, email: str) -> Dict:
    """Handle user login with idToken validation and user creation/retrieval"""
    try:
        if not email:
            logger.warning("Token missing email claim")
            raise HTTPException(status_code=400, detail="Email claim not found in token")

        logger.info(f"User authenticated: {email}")

        # Check if user exists in Cosmos DB
        user_data = await cosmos_client.get_user_data(email)

        if not user_data:
            logger.info(f"Creating new user account for: {email}")

            # Fetch admin template for new user creation
            admin_template = await cosmos_client.get_user_data("roundtable_ai_admin")
            if not admin_template:
                logger.error("Admin template not found in database")
                raise HTTPException(status_code=500, detail="User template not found")

            # Clone admin template and update user-specific fields
            new_user = copy.deepcopy(admin_template)

            # Update user_id in cloned groups and meetings to the new user's email
            for group in new_user.get("groups", []):
                group["user_id"] = email
            for meeting in new_user.get("meetings", []):
                meeting["user_id"] = email

            new_user["id"] = email
            new_user["email"] = email
            new_user["display_name"] = name
            new_user["_rid"] = None
            new_user["_self"] = None
            new_user["_etag"] = None
            new_user["_attachments"] = None
            new_user["_ts"] = None

            # Create new user in Cosmos DB using upsert_item with the full new_user object
            created_user = cosmos_client.container.upsert_item(body=new_user)  # Use upsert_item directly
            logger.info(f"New user created: {email}")
            # Add 'name' field mapped from 'display_name' and return the full created user data
            created_user["name"] = created_user.get("display_name")
            return created_user
        else:
            # Mask API keys in llmAccounts.providers before returning
            if user_data and "llmAccounts" in user_data and "providers" in user_data["llmAccounts"]:
                providers = user_data["llmAccounts"].get("providers", [])
                if isinstance(providers, list):
                    for provider in providers:
                        if isinstance(provider, dict) and "api_key" in provider:
                            provider["api_key"] = "SECRET"

        logger.info(f"Existing user logged in: {email}")
        # Add 'name' field mapped from 'display_name' and return the full existing user data
        user_data["name"] = user_data.get("display_name")
        return user_data

    except HTTPException:
        # Re-raise HTTP exceptions without modification
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

        # Map fields for response, matching UserProfileResponse
        response = {"id": user_data.get("id"), "name": user_data.get("display_name", ""), "email": user_data.get("email", "")}

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
        # Map fields for response, matching UserDetailResponse
        response = {
            "id": user_data.get("id"),
            "name": user_data.get("display_name", ""),  # Map display_name to name
            "email": user_data.get("email", ""),
            # Include other fields expected by UserDetailResponse (or add them to the model)
            # For now, just mapping the base fields and counts
            "llm_providers_count": len(user_data.get("llmAccounts", {}).get("providers", [])),
            "participants_count": len(user_data.get("participants", [])),
            "meetings_count": len(user_data.get("meetings", [])),
            "groups_count": len(user_data.get("groups", [])),
            "chat_sessions_count": len(user_data.get("chat_sessions", [])),  # Assuming this might be needed later
        }

        logger.info("Successfully retrieved detailed user information for: %s", user_id)
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching detailed user information for %s: %s", user_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while retrieving detailed user information")
