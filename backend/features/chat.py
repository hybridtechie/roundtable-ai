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
    chatroom_id: str
    message: str

def get_llm_client():
    return LLMClient(provider="azure")

def format_sse_event(event_type: str, data: dict) -> str:
    """Format data into SSE event string"""
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

# Utility Methods
def fetch_chatroom_data(chatroom_id: str) -> tuple[list, str]:
    """Fetch chatroom details from SQLite."""
    conn = sqlite3.connect("agents.db")
    cursor = conn.cursor()
    cursor.execute("SELECT agent_ids, topic FROM chatrooms WHERE id = ?", (chatroom_id,))
    chatroom_data = cursor.fetchone()
    conn.close()
    
    if not chatroom_data:
        raise HTTPException(status_code=404, detail=f"Chatroom ID '{chatroom_id}' not found")
    
    agent_ids = json.loads(chatroom_data[0])
    topic = chatroom_data[1]
    
    if not topic:
        raise HTTPException(status_code=400, detail="Chatroom has no topic set. Please set a topic first.")
    
    return agent_ids, topic

def fetch_agents_data(agent_ids: list) -> dict:
    """Fetch agent details from SQLite and ChromaDB."""
    agents_data = {}
    conn = sqlite3.connect("agents.db")
    cursor = conn.cursor()
    
    try:
        for agent_id in agent_ids:
            cursor.execute("SELECT name, persona_description FROM agents WHERE id = ?", (agent_id,))
            result = cursor.fetchone()
            if not result:
                raise HTTPException(status_code=404, detail=f"Agent ID '{agent_id}' not found")
            
            name, persona_description = result
            chroma_results = collection.get(ids=[agent_id])
            context = chroma_results["documents"][0] if chroma_results["documents"] else None
            
            agents_data[agent_id] = {
                "name": name,
                "persona_description": persona_description,
                "context": context
            }
    finally:
        conn.close()
    
    return agents_data

def generate_agent_response(llm_client, agent_info: dict, topic: str, step: str, message: str) -> str:
    """Generate a response for an agent based on their persona and context."""
    system_prompt = (
        f"You are {agent_info['name']} with persona: {agent_info['persona_description']}. "
        f"Context: {agent_info['context']}. You are in a chatroom discussing '{topic}'. "
        f"The current agenda step is: '{step}'. Respond based on your role and the user's message: '{message}'."
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": message}
    ]
    response = llm_client.send_request(messages)
    # Handle both string and object responses
    return response.get('content', response) if isinstance(response, dict) else response

def synthesize_final_response(llm_client, topic: str, message: str, discussion_log: list) -> str:
    """Synthesize a final response from the discussion log."""
    synthesis_prompt = (
        f"You are the Orchestrator. Below is the discussion log from a chatroom on the topic '{topic}':\n"
        f"{json.dumps(discussion_log, indent=2)}\n"
        f"Based on the agents' contributions and the user's message '{message}', provide a detailed, coherent response."
    )
    synthesis_messages = [
        {"role": "system", "content": synthesis_prompt},
        {"role": "user", "content": "Synthesize the discussion into a final response."}
    ]
    response = llm_client.send_request(synthesis_messages)
    # Handle both string and object responses
    return response.get('content', response) if isinstance(response, dict) else response

# Refactored Methods
async def stream_chatroom_discussion(chatroom_id: str, message: str):
    """Stream chatroom discussion with SSE."""
    async def event_generator():
        try:
            agent_ids, topic = fetch_chatroom_data(chatroom_id)
            agents_data = fetch_agents_data(agent_ids)
            llm_client = get_llm_client()
            agenda = [
                "Introduce your perspective on the topic",
                "Discuss pros and cons",
                "Provide a recommendation"
            ]

            for step in agenda:
                for agent_id, agent_info in agents_data.items():
                    response = generate_agent_response(llm_client, agent_info, topic, step, message)
                    yield format_sse_event("agent_response", {
                        "agent_id": agent_id,
                        "name": agent_info["name"],
                        "step": step,
                        "response": response
                    })
                    await asyncio.sleep(0.1)

            # Synthesize final response
            discussion_log = [
                {"agent_id": agent_id, "name": info["name"], "step": step, "response": response}
                for step in agenda
                for agent_id, info in agents_data.items()
                for response in [generate_agent_response(llm_client, info, topic, step, message)]
            ]
            final_response = synthesize_final_response(llm_client, topic, message, discussion_log)
            yield format_sse_event("final_response", {"response": final_response})
            yield format_sse_event("complete", {})

        except HTTPException as e:
            yield format_sse_event("error", {"detail": str(e.detail)})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={'Cache-Control': 'no-cache', 'Connection': 'keep-alive'}
    )

async def start_chatroom_discussion(chatroom_id: str, message: str):
    """Simulate a chatroom discussion among agents with an orchestrator."""
    agent_ids, topic = fetch_chatroom_data(chatroom_id)
    agents_data = fetch_agents_data(agent_ids)
    llm_client = get_llm_client()
    discussion_log = []
    agenda = [
        "Introduce your perspective on the topic",
        "Discuss pros and cons",
        "Provide a recommendation"
    ]

    for step in agenda:
        for agent_id, agent_info in agents_data.items():
            response = generate_agent_response(llm_client, agent_info, topic, step, message)
            discussion_log.append({
                "agent_id": agent_id,
                "name": agent_info["name"],
                "step": step,
                "response": response
            })

    final_response = synthesize_final_response(llm_client, topic, message, discussion_log)
    return {"discussion_log": discussion_log, "final_response": final_response}