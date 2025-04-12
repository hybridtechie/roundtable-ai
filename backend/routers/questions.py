from fastapi import APIRouter, Depends, HTTPException, Query
from logger_config import setup_logger
from features.questions import generate_questions
from models import QuestionsResponse
from auth import UserClaims, validate_token

logger = setup_logger(__name__)

router = APIRouter(prefix="/questions", tags=["Questions"])

@router.get("", summary="Generate questions based on topic and group context")
async def generate_questions_endpoint(
    topic: str = Query(..., description="The topic to generate questions about"),
    group_id: str = Query(..., description="The ID of the group providing context"),
    current_user: UserClaims = Depends(validate_token),
):
    """
    Generates relevant questions based on a given topic and the context
    derived from a specified group. Requires authentication.
    """
    try:
        user_id = current_user.email
        logger.info("User '%s' requesting question generation for topic: '%s', group_id: %s", user_id, topic, group_id)

        result = await generate_questions(topic, group_id, user_id)

        if not result or not result.questions:
            logger.warning("Question generation returned no questions for topic '%s', group %s, user %s", topic, group_id, user_id)

        logger.info("Successfully generated questions for topic '%s', group %s, user %s", topic, group_id, user_id)
        return result  # Should match QuestionsResponse model

    except Exception as e:
        logger.error("Failed to generate questions for topic '%s', group %s, user %s: %s", topic, group_id, user_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate questions: {str(e)}")
