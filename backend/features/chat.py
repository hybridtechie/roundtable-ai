from pydantic import BaseModel
from utils_llm import LLMClient  # Assuming this exists
import os
from dotenv import load_dotenv
import sqlite3
import json
from utils_llm import LLMClient  # Assuming this exists
from fastapi import HTTPException
from db import collection  # Import ChromaDB collection

# Load environment variables
load_dotenv()

class ChatMessage(BaseModel):
    chatroom_id: str
    message: str
def get_llm_client():
    return LLMClient(provider="azure")  # Adjust provider as needed

async def start_chatroom_discussion(chatroom_id: str, message: str):
    """Simulate a chatroom discussion among agents with an orchestrator."""
    # Connect to SQLite to fetch chatroom details
    conn = sqlite3.connect("agents.db")
    cursor = conn.cursor()
    cursor.execute("SELECT agent_ids, topic FROM chatrooms WHERE id = ?", (chatroom_id,))
    chatroom_data = cursor.fetchone()
    if not chatroom_data:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Chatroom ID '{chatroom_id}' not found")
    
    agent_ids_json, topic = chatroom_data
    agent_ids = json.loads(agent_ids_json)
    conn.close()

    if not topic:
        raise HTTPException(status_code=400, detail="Chatroom has no topic set. Please set a topic first.")

    # Fetch agent details from SQLite and ChromaDB
    agents_data = {}
    conn = sqlite3.connect("agents.db")
    cursor = conn.cursor()
    for agent_id in agent_ids:
        cursor.execute("SELECT name, persona_description FROM agents WHERE id = ?", (agent_id,))
        result = cursor.fetchone()
        if not result:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Agent ID '{agent_id}' not found")
        
        name, persona_description = result
        chroma_results = collection.get(ids=[agent_id])
        if not chroma_results["documents"]:
            # conn.close()
            chroma_results = None
            # raise HTTPException(status_code=404, detail=f"Context for agent ID '{agent_id}' not found")
        
        context = None # Set this to context. Adjust as needed
        agents_data[agent_id] = {
            "name": name,
            "persona_description": persona_description,
            "context": context
        }
    conn.close()

    # Orchestrator logic
    llm_client = get_llm_client()
    discussion_log = []
    agenda = [
        "Introduce your perspective on the topic",
        "Discuss pros and cons",
        "Provide a recommendation"
    ]

    # Simulate turn-based discussion
    for step in agenda:
        for agent_id, agent_info in agents_data.items():
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
            discussion_log.append({
                "agent_id": agent_id,
                "name": agent_info["name"],
                "step": step,
                "response": response
            })

    # Synthesize a final response
    synthesis_prompt = (
        f"You are the Orchestrator. Below is the discussion log from a chatroom on the topic '{topic}':\n"
        f"{json.dumps(discussion_log, indent=2)}\n"
        f"Based on the agents' contributions and the user's message '{message}', provide a detailed, coherent response."
    )
    synthesis_messages = [
        {"role": "system", "content": synthesis_prompt},
        {"role": "user", "content": "Synthesize the discussion into a final response."}
    ]
    final_response = llm_client.send_request(synthesis_messages)

    return {
        "discussion_log": discussion_log,
        "final_response": final_response
    }