from fastapi import APIRouter, Depends, HTTPException
from logger_config import setup_logger

from features.user import login_user, get_me, get_me_detail

from models import UserProfileResponse, UserDetailResponse

from auth import UserClaims, validate_token

logger = setup_logger(__name__)

router_user = APIRouter(prefix="/user", tags=["User Profile"])

@router_user.post("/login", summary="Process user login via token validation")
async def login_endpoint(current_user: UserClaims = Depends(validate_token)):
    try:
        user_email = current_user.email
        user_name = current_user.name
        logger.info("Processing login request for user: %s", user_email)
        result = await login_user(user_name, user_email)
        if not result:
            logger.error("Login feature function returned None for user: %s", user_email)
            raise HTTPException(status_code=500, detail="Login process failed internally.")
        logger.info("Successfully processed login for user: %s", user_email)
        return result
    except Exception as e:
        logger.error("Login failed for user %s: %s", current_user.email if current_user else "Unknown", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@router_user.get("/me", response_model=UserProfileResponse, summary="Get basic profile information for the authenticated user")
async def get_user_info_endpoint(current_user: UserClaims = Depends(validate_token)):
    try:
        user_id = current_user.email
        logger.info("Fetching basic user information for user: %s", user_id)
        result = await get_me(user_id)
        if result is None:
            logger.warning("Basic profile not found for user: %s", user_id)
            raise HTTPException(status_code=404, detail="User profile not found.")
        logger.info("Successfully retrieved basic user information for: %s", user_id)
        return result
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error("Failed to fetch basic user information for %s: %s", current_user.email, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch user information: {str(e)}")

@router_user.get("/me/detail", response_model=UserDetailResponse, summary="Get detailed profile information for the authenticated user")
async def get_user_detail_endpoint(current_user: UserClaims = Depends(validate_token)):
    try:
        user_id = current_user.email
        logger.info("Fetching detailed user information for user: %s", user_id)
        result = await get_me_detail(user_id)
        if result is None:
            logger.warning("Detailed profile not found for user: %s", user_id)
            raise HTTPException(status_code=404, detail="User detailed profile not found.")
        logger.info("Successfully retrieved detailed user information for: %s", user_id)
        response_data = result.copy()
        response_data["id"] = response_data.pop("user_id", None)
        response_data["name"] = response_data.pop("display_name", None)
        return response_data
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error("Failed to fetch detailed user information for %s: %s", current_user.email, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch detailed user information: {str(e)}")
