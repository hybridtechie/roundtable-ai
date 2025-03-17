from pydantic import BaseModel
from utils_llm import LLMClient
import os
from dotenv import load_dotenv
import sqlite3
import json
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from db import collection
import asyncio
from logger_config import setup_logger

# Set up logger
logger = setup_logger(__name__)

# Load environment variables
load_dotenv()


class ChatMessage(BaseModel):
    meeting_id: str
    message: str


def get_llm_client():
    try:
        client = LLMClient(provider="azure")
        logger.debug("Successfully initialized Azure LLM client")
        return client
    except Exception as e:
        logger.error("Failed to initialize LLM client: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to initialize LLM client")


def format_sse_event(event_type: str, data: dict) -> str:
    """Format data into SSE event string"""
    try:
        event_str = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
        logger.debug("Formatted SSE event: %s", event_type)
        return event_str
    except Exception as e:
        logger.error("Failed to format SSE event: %s", str(e), exc_info=True)
        raise


# Utility Methods
def fetch_group_data(group_id: str) -> tuple[list, str]:
    """Fetch meeting details from SQLite."""
    logger.info("Fetching meeting data for ID: %s", group_id)
    conn = None
    try:
        conn = sqlite3.connect("roundtableai.db")
        cursor = conn.cursor()
        cursor.execute("SELECT participant_ids FROM groups WHERE id = ?", (group_id,))
        group_data = cursor.fetchone()

        if not group_data:
            logger.error("Group not found: %s", group_id)
            raise HTTPException(status_code=404, detail=f"Meeting ID '{group_id}' not found")

        participant_ids = json.loads(group_data[0])

        logger.info("Successfully fetched meeting data with %d participants", len(participant_ids))
        return participant_ids

    except json.JSONDecodeError as e:
        logger.error("Failed to parse participant_ids JSON for meeting %s: %s", group_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Invalid participant data format in database")
    except sqlite3.Error as e:
        logger.error("Database error while fetching meeting %s: %s", group_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Database error while fetching meeting data")
    except Exception as e:
        logger.error("Unexpected error while fetching meeting %s: %s", group_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while fetching meeting data")
    finally:
        if conn:
            conn.close()


def fetch_participants_data(participant_ids: list) -> dict:
    """Fetch Participant details from SQLite and ChromaDB."""
    logger.info("Fetching data for %d participants", len(participant_ids))
    participants_data = {}
    conn = None

    try:
        conn = sqlite3.connect("roundtableai.db")
        cursor = conn.cursor()

        for participant_id in participant_ids:
            try:
                cursor.execute("SELECT name, persona_description FROM participants WHERE id = ?", (participant_id,))
                result = cursor.fetchone()
                if not result:
                    logger.error("Participant not found: %s", participant_id)
                    raise HTTPException(status_code=404, detail=f"Participant ID '{participant_id}' not found")

                name, persona_description = result

                logger.debug("Fetching ChromaDB data for participant: %s", participant_id)
                chroma_results = collection.get(ids=[participant_id])
                context = chroma_results["documents"][0] if chroma_results["documents"] else None

                if not context:
                    logger.warning("No context found in ChromaDB for participant: %s", participant_id)

                participants_data[participant_id] = {"name": name, "persona_description": persona_description, "context": context}
                logger.debug("Successfully fetched data for participant: %s", name)

            except Exception as e:
                logger.error("Error processing participant %s: %s", participant_id, str(e), exc_info=True)
                raise

        logger.info("Successfully fetched data for all participants")
        return participants_data

    except Exception as e:
        logger.error("Failed to fetch participants data: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch participants data")
    finally:
        if conn:
            conn.close()


def generate_participant_response(llm_client, participant_info: dict, step: str, message: str) -> str:
    """Generate a response for an Participant based on their persona and context."""
    try:
        logger.info("Generating response for participant: %s, step: %s", participant_info["name"], step)

        system_prompt = (
            f"You are {participant_info['name']} with persona: {participant_info['persona_description']}. "
            f"Context: {participant_info['context']}. You are in a meeting discussing '{message}'. "
            f"The current agenda step is: '{step}'. Respond based on your role and the user's message: '{message}'."
        )
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": message}]

        logger.debug("Sending request to LLM for participant: %s", participant_info["name"])
        response = llm_client.send_request(messages)

        # Handle both string and object responses
        result = response.get("content", response) if isinstance(response, dict) else response
        logger.info("Successfully generated response for participant: %s", participant_info["name"])
        return result

    except Exception as e:
        logger.error("Failed to generate response for participant %s: %s", participant_info["name"], str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate response for participant {participant_info['name']}")


def synthesize_final_response(llm_client, topic: str, message: str, discussion_log: list) -> str:
    """Synthesize a final response from the discussion log."""
    try:
        logger.info("Synthesizing final response for topic: %s", topic)

        synthesis_prompt = (
            f"You are the Orchestrator. Below is the discussion log from a meeting on the topic '{topic}':\n"
            f"{json.dumps(discussion_log, indent=2)}\n"
            f"Based on the Participants' contributions and the user's message '{message}', provide a detailed, coherent response."
        )
        synthesis_messages = [{"role": "system", "content": synthesis_prompt}, {"role": "user", "content": "Synthesize the discussion into a final response."}]

        logger.debug("Sending synthesis request to LLM")
        response = llm_client.send_request(synthesis_messages)

        # Handle both string and object responses
        result = response.get("content", response) if isinstance(response, dict) else response
        logger.info("Successfully synthesized final response")
        return result

    except Exception as e:
        logger.error("Failed to synthesize final response: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to synthesize final response")


async def stream_meeting_discussion(group_id: str, message: str):
    """Stream meeting discussion with SSE."""
    logger.info("Starting streaming discussion for meeting: %s", group_id)

    async def event_generator():
        try:
            participant_ids = fetch_group_data(group_id)
            participants_data = fetch_participants_data(participant_ids)
            llm_client = get_llm_client()
            agenda = ["Introduce your perspective on the topic", "Discuss pros and cons", "Provide a recommendation"]

            for step in agenda:
                logger.debug("Processing agenda step: %s", step)
                for participant_id, participant_info in participants_data.items():
                    try:
                        response = generate_participant_response(llm_client, participant_info, step, message)
                        yield format_sse_event("participant_response", {"participant_id": participant_id, "name": participant_info["name"], "step": step, "response": response})
                        await asyncio.sleep(0.1)
                    except Exception as e:
                        logger.error("Error generating response for participant %s: %s", participant_info["name"], str(e), exc_info=True)
                        yield format_sse_event("error", {"detail": f"Error generating response for {participant_info['name']}"})

            # Synthesize final response
            logger.debug("Generating discussion log for final synthesis")
            discussion_log = [
                {"participant_id": participant_id, "name": info["name"], "step": step, "response": generate_participant_response(llm_client, info, step, message)}
                for step in agenda
                for participant_id, info in participants_data.items()
            ]

            final_response = synthesize_final_response(llm_client, message, discussion_log)
            yield format_sse_event("final_response", {"response": final_response})
            yield format_sse_event("complete", {})
            logger.info("Successfully completed streaming discussion")

        except HTTPException as e:
            logger.error("HTTP error in stream: %s", str(e.detail))
            yield format_sse_event("error", {"detail": str(e.detail)})
        except Exception as e:
            logger.error("Unexpected error in stream: %s", str(e), exc_info=True)
            yield format_sse_event("error", {"detail": "Internal server error during streaming"})

    return StreamingResponse(event_generator(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "Connection": "keep-alive"})


async def start_meeting_discussion(meeting_id: str, message: str):
    """Simulate a meeting discussion among Participants with an orchestrator."""
    logger.info("Starting meeting discussion for meeting: %s", meeting_id)

    try:
        participant_ids, topic = fetch_group_data(meeting_id)
        participants_data = fetch_participants_data(participant_ids)
        llm_client = get_llm_client()
        discussion_log = []
        agenda = ["Introduce your perspective on the topic", "Discuss pros and cons", "Provide a recommendation"]

        for step in agenda:
            logger.debug("Processing agenda step: %s", step)
            for participant_id, participant_info in participants_data.items():
                try:
                    response = generate_participant_response(llm_client, participant_info, topic, step, message)
                    discussion_log.append({"participant_id": participant_id, "name": participant_info["name"], "step": step, "response": response})
                except Exception as e:
                    logger.error("Error generating response for participant %s: %s", participant_info["name"], str(e), exc_info=True)
                    raise HTTPException(status_code=500, detail=f"Failed to generate response for {participant_info['name']}")

        final_response = synthesize_final_response(llm_client, topic, message, discussion_log)
        logger.info("Successfully completed meeting discussion")
        return {"discussion_log": discussion_log, "final_response": final_response}

    except Exception as e:
        logger.error("Failed to complete meeting discussion: %s", str(e), exc_info=True)
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail="Failed to complete meeting discussion")
