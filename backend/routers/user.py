from fastapi import APIRouter, Depends, HTTPException
from logger_config import setup_logger

# Feature imports
from features.user import login_user, get_me, get_me_detail

# Model imports
# Use absolute import from 'backend' directory perspective
from models import UserProfileResponse, UserDetailResponse  # Assuming login returns UserProfileResponse

# Auth imports
from auth import UserClaims, validate_token

# Logger setup
logger = setup_logger(__name__)

router_user = APIRouter(prefix="/user", tags=["User Profile"])


# --- Authentication Endpoint ---


@router_user.post("/login", summary="Process user login via token validation")
async def login_endpoint(current_user: UserClaims = Depends(validate_token)):
    """
    Validates the user's token and logs them in (e.g., creates/updates user record in DB).
    Requires a valid authentication token in the Authorization header.
    Returns basic user profile information upon successful login/validation.
    """
    try:
        user_email = current_user.email
        user_name = current_user.name
        logger.info("Processing login request for user: %s", user_email)
        # login_user likely creates or fetches user data based on token claims
        result = await login_user(user_name, user_email)
        # Ensure result matches UserProfileResponse structure
        if not result:
            logger.error("Login feature function returned None for user: %s", user_email)
            raise HTTPException(status_code=500, detail="Login process failed internally.")
        logger.info("Successfully processed login for user: %s", user_email)
        return result
    except Exception as e:
        logger.error("Login failed for user %s: %s", current_user.email if current_user else "Unknown", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


# --- User Profile Endpoints ---


@router_user.get("/me", response_model=UserProfileResponse, summary="Get basic profile information for the authenticated user")
async def get_user_info_endpoint(current_user: UserClaims = Depends(validate_token)):
    """
    Retrieves basic profile information (ID, name, email) for the currently authenticated user.
    Requires a valid authentication token.
    """
    try:
        user_id = current_user.email  # Use email from token as the user identifier
        logger.info("Fetching basic user information for user: %s", user_id)
        # Assuming get_me fetches user data based on the identifier (email)
        result = await get_me(user_id)
        if result is None:
            logger.warning("Basic profile not found for user: %s", user_id)
            raise HTTPException(status_code=404, detail="User profile not found.")
        logger.info("Successfully retrieved basic user information for: %s", user_id)
        return result  # Should match UserProfileResponse
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error("Failed to fetch basic user information for %s: %s", current_user.email, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch user information: {str(e)}")


@router_user.get("/me/detail", response_model=UserDetailResponse, summary="Get detailed profile information for the authenticated user")
async def get_user_detail_endpoint(current_user: UserClaims = Depends(validate_token)):
    """
    Retrieves detailed profile information for the currently authenticated user,
    potentially including associated groups, meetings, etc.
    Requires a valid authentication token.
    """
    try:
        user_id = current_user.email  # Use email from token
        logger.info("Fetching detailed user information for user: %s", user_id)
        # Assuming get_me_detail fetches comprehensive user data
        result = await get_me_detail(user_id)
        if result is None:
            logger.warning("Detailed profile not found for user: %s", user_id)
            raise HTTPException(status_code=404, detail="User detailed profile not found.")
        logger.info("Successfully retrieved detailed user information for: %s", user_id)
        # Map fields from get_me_detail result to UserDetailResponse model
        response_data = result.copy()  # Create a copy to modify
        response_data["id"] = response_data.pop("user_id", None)
        response_data["name"] = response_data.pop("display_name", None)
        return response_data  # Return the mapped data
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error("Failed to fetch detailed user information for %s: %s", current_user.email, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch detailed user information: {str(e)}")


# Include both routers when updating main.py
# app.include_router(router_login)
# app.include_router(router_user)
