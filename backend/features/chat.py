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

# Load environment variables
load_dotenv()


class ChatMessage(BaseModel):
    meeting_id: str
    message: str


def get_llm_client():
    return LLMClient(provider="azure")


def format_sse_event(event_type: str, data: dict) -> str:
    """Format data into SSE event string"""
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


# Utility Methods
def fetch_meeting_data(meeting_id: str) -> tuple[list, str]:
    """Fetch meeting details from SQLite."""
    conn = sqlite3.connect("aitwins.db")
    cursor = conn.cursor()
    cursor.execute("SELECT aitwin_ids, topic FROM meetings WHERE id = ?", (meeting_id,))
    meeting_data = cursor.fetchone()
    conn.close()

    if not meeting_data:
        raise HTTPException(status_code=404, detail=f"Meeting ID '{meeting_id}' not found")

    aitwin_ids = json.loads(meeting_data[0])
    topic = meeting_data[1]

    if not topic:
        raise HTTPException(status_code=400, detail="Meeting has no topic set. Please set a topic first.")

    return aitwin_ids, topic


def fetch_aitwins_data(aitwin_ids: list) -> dict:
    """Fetch AiTwin details from SQLite and ChromaDB."""
    aitwins_data = {}
    conn = sqlite3.connect("aitwins.db")
    cursor = conn.cursor()

    try:
        for aitwin_id in aitwin_ids:
            cursor.execute("SELECT name, persona_description FROM aitwins WHERE id = ?", (aitwin_id,))
            result = cursor.fetchone()
            if not result:
                raise HTTPException(status_code=404, detail=f"AiTwin ID '{aitwin_id}' not found")

            name, persona_description = result
            chroma_results = collection.get(ids=[aitwin_id])
            context = chroma_results["documents"][0] if chroma_results["documents"] else None

            aitwins_data[aitwin_id] = {"name": name, "persona_description": persona_description, "context": context}
    finally:
        conn.close()

    return aitwins_data


def generate_aitwin_response(llm_client, aitwin_info: dict, topic: str, step: str, message: str) -> str:
    """Generate a response for an AiTwin based on their persona and context."""
    system_prompt = (
        f"You are {aitwin_info['name']} with persona: {aitwin_info['persona_description']}. "
        f"Context: {aitwin_info['context']}. You are in a meeting discussing '{topic}'. "
        f"The current agenda step is: '{step}'. Respond based on your role and the user's message: '{message}'."
    )
    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": message}]
    response = llm_client.send_request(messages)
    # Handle both string and object responses
    return response.get("content", response) if isinstance(response, dict) else response


def synthesize_final_response(llm_client, topic: str, message: str, discussion_log: list) -> str:
    """Synthesize a final response from the discussion log."""
    synthesis_prompt = (
        f"You are the Orchestrator. Below is the discussion log from a meeting on the topic '{topic}':\n"
        f"{json.dumps(discussion_log, indent=2)}\n"
        f"Based on the AiTwins' contributions and the user's message '{message}', provide a detailed, coherent response."
    )
    synthesis_messages = [{"role": "system", "content": synthesis_prompt}, {"role": "user", "content": "Synthesize the discussion into a final response."}]
    response = llm_client.send_request(synthesis_messages)
    # Handle both string and object responses
    return response.get("content", response) if isinstance(response, dict) else response


# Refactored Methods
async def stream_meeting_discussion(meeting_id: str, message: str):
    """Stream meeting discussion with SSE."""

    async def event_generator():
        try:
            aitwin_ids, topic = fetch_meeting_data(meeting_id)
            aitwins_data = fetch_aitwins_data(aitwin_ids)
            llm_client = get_llm_client()
            agenda = ["Introduce your perspective on the topic", "Discuss pros and cons", "Provide a recommendation"]

            for step in agenda:
                for aitwin_id, aitwin_info in aitwins_data.items():
                    response = generate_aitwin_response(llm_client, aitwin_info, topic, step, message)
                    yield format_sse_event("aitwin_response", {"aitwin_id": aitwin_id, "name": aitwin_info["name"], "step": step, "response": response})
                    await asyncio.sleep(0.1)

            # Synthesize final response
            discussion_log = [
                {"aitwin_id": aitwin_id, "name": info["name"], "step": step, "response": response}
                for step in agenda
                for aitwin_id, info in aitwins_data.items()
                for response in [generate_aitwin_response(llm_client, info, topic, step, message)]
            ]
            final_response = synthesize_final_response(llm_client, topic, message, discussion_log)
            yield format_sse_event("final_response", {"response": final_response})
            yield format_sse_event("complete", {})

        except HTTPException as e:
            yield format_sse_event("error", {"detail": str(e.detail)})

    return StreamingResponse(event_generator(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "Connection": "keep-alive"})


async def start_meeting_discussion(meeting_id: str, message: str):
    """Simulate a meeting discussion among AiTwins with an orchestrator."""
    aitwin_ids, topic = fetch_meeting_data(meeting_id)
    aitwins_data = fetch_aitwins_data(aitwin_ids)
    llm_client = get_llm_client()
    discussion_log = []
    agenda = ["Introduce your perspective on the topic", "Discuss pros and cons", "Provide a recommendation"]

    for step in agenda:
        for aitwin_id, aitwin_info in aitwins_data.items():
            response = generate_aitwin_response(llm_client, aitwin_info, topic, step, message)
            discussion_log.append({"aitwin_id": aitwin_id, "name": aitwin_info["name"], "step": step, "response": response})

    final_response = synthesize_final_response(llm_client, topic, message, discussion_log)
    return {"discussion_log": discussion_log, "final_response": final_response}
