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
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE") # Keep for potential future use with access tokens
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID") # Add Client ID for ID token validation

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
        key = get_key_from_jwks(jwks, kid) # This function already raises HTTPException if key not found

        # Decode and validate the token using the public key from JWKS
        # Note: python-jose requires the key in JWK format
        payload = jwt.decode(
            id_token,
            key=key,
            algorithms=['RS256'], # Standard algorithm for Auth0 RS256 signed tokens
            audience=AUTH0_CLIENT_ID, # Use Client ID for ID token audience validation
            issuer=f"https://{AUTH0_DOMAIN}/" # Validate the issuer
            # Standard claims like exp, iat, iss, aud are verified by default by python-jose
        )

        logger.info("ID token validated successfully for issuer: %s", payload.get("iss"))
        return payload
    except JWTError as e:
        logger.error("ID Token validation failed: %s", str(e))
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    except HTTPException as e: # Re-raise HTTPExceptions from helpers
        raise e
    except Exception as e: # Catch other potential errors during validation
        logger.error("An unexpected error occurred during token validation: %s", str(e))
        raise HTTPException(status_code=500, detail="Token validation error")
# Removed extract_email_from_token as login_user handles payload directly
# Removed unused chat_sessions_count variable
async def login_user(authorization: str = Header(...)) -> Dict:
    """Handle user login with idToken validation and user creation/retrieval"""
    try:
        # Extract token from Authorization header
        if not authorization.startswith("Bearer "):
            logger.warning("Invalid authorization header format")
            raise HTTPException(status_code=401, detail="Invalid authorization header format. Expected 'Bearer <token>'")
        
        id_token = authorization.split(" ")[1]
        if not id_token:
            raise HTTPException(status_code=401, detail="Empty token provided")

        # Validate token and extract user information
        payload = await validate_id_token(id_token)
        
        # Extract required user information from token claims
        email = payload.get("email")
        name = payload.get("name", "")  # Use empty string as fallback if name not in token
        
        if not email:
            logger.warning("Token missing email claim")
            raise HTTPException(status_code=400, detail="Email claim not found in token")

        logger.info(f"User authenticated: {email}")
        
        # Check if user exists in Cosmos DB
        user_data = await cosmos_client.get_user_by_email(email)
        
        if not user_data:
            logger.info(f"Creating new user account for: {email}")
            
            # Fetch admin template for new user creation
            admin_template = await cosmos_client.get_user_data("roundtable_ai_admin")
            if not admin_template:
                logger.error("Admin template not found in database")
                raise HTTPException(status_code=500, detail="User template not found")
            
            # Clone admin template and update user-specific fields
            new_user = copy.deepcopy(admin_template)
            new_user["id"] = email
            new_user["email"] = email
            new_user["display_name"] = name
            
            # Create new user in Cosmos DB
            await cosmos_client.create_user(new_user)
            logger.info(f"New user created: {email}")
            return await get_me(email)
        
        logger.info(f"Existing user logged in: {email}")
        return await get_me(email)

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
