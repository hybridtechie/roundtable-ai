from pydantic import BaseModel
from utils_llm import LLMClient
from fastapi import HTTPException
from logger_config import setup_logger
from prompts import generate_questions_prompt
from features.group import get_group

# Set up logger
logger = setup_logger(__name__)


class QuestionResponse(BaseModel):
    questions: list[str]


async def generate_questions(topic: str, group_id: str, user_id: str) -> QuestionResponse:
    """Generate questions based on topic and group context."""
    try:
        logger.info("Generating questions for topic: %s, group: %s, user: %s", topic, group_id, user_id)

        # Fetch group details
        group = await get_group(group_id, user_id)
        if not group:
            raise HTTPException(status_code=404, detail=f"Group {group_id} not found")

        # Get LLM client with user's configuration
        from features.chat import get_llm_client  # Import here to avoid circular import

        llm_client = await get_llm_client(user_id)

        # Get prompt from prompts.py
        prompt = generate_questions_prompt(topic, group)

        # Generate questions using LLM
        messages = [{"role": "system", "content": prompt}]
        response, _ = llm_client.send_request(messages)

        # Process response into list of questions
        questions = [line.strip()[3:] for line in response.strip().split("\n") if line.strip()]

        if len(questions) < 5:
            logger.error("Not enough questions generated: %d", len(questions))
            raise HTTPException(status_code=500, detail="Failed to generate sufficient questions")

        logger.info("Successfully generated %d questions", len(questions))
        return QuestionResponse(questions=questions)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to generate questions: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate questions: {str(e)}")
