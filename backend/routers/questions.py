from fastapi import APIRouter, Depends, HTTPException, Query
from logger_config import setup_logger

# Feature imports
from features.questions import generate_questions

# Model imports
# Use absolute import from 'backend' directory perspective
from models import QuestionsResponse

# Auth imports
from auth import UserClaims, validate_token

# Logger setup
logger = setup_logger(__name__)

# Create an APIRouter instance
router = APIRouter(
    prefix="/questions",    # Prefix for all routes in this router
    tags=["Questions"]      # Tag for OpenAPI documentation
)

# --- Generate Questions Endpoint ---

@router.get("", response_model=QuestionsResponse, summary="Generate questions based on topic and group context") # Route is now /questions
async def generate_questions_endpoint(
    topic: str = Query(..., description="The topic to generate questions about"),
    group_id: str = Query(..., description="The ID of the group providing context"),
    current_user: UserClaims = Depends(validate_token)
):
    """
    Generates relevant questions based on a given topic and the context
    derived from a specified group. Requires authentication.
    """
    try:
        user_id = current_user.email
        logger.info("User '%s' requesting question generation for topic: '%s', group_id: %s", user_id, topic, group_id)

        # Call the feature function with topic, group_id, and user_id
        # Assuming generate_questions returns a dict matching QuestionsResponse
        result = await generate_questions(topic, group_id, user_id)

        # Add check if result is valid (e.g., not None or empty) if necessary
        if not result or not result.get("questions"):
             logger.warning("Question generation returned no questions for topic '%s', group %s, user %s", topic, group_id, user_id)
             # Decide if this is an error or just an empty result. Returning empty list might be okay.
             # raise HTTPException(status_code=404, detail="Could not generate questions for the given topic and group context.")

        logger.info("Successfully generated questions for topic '%s', group %s, user %s", topic, group_id, user_id)
        return result # Should match QuestionsResponse model

    except Exception as e:
        logger.error("Failed to generate questions for topic '%s', group %s, user %s: %s", topic, group_id, user_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate questions: {str(e)}")