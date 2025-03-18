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
from features.meeting import create_meeting, MeetingCreate

# Set up logger
logger = setup_logger(__name__)

# Define input model (matching main.py's chat-stream endpoint)
class ChatMessage(BaseModel):
    group_id: str
    strategy: str
    topic: str
    message: str  # User message to contextualize the discussion

# LLM client initialization
def get_llm_client():
    try:
        client = LLMClient(provider="azure")  # Adjust provider as needed
        logger.debug("Initialized LLM client")
        return client
    except Exception as e:
        logger.error("Failed to initialize LLM client: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to initialize LLM client")

# SSE event formatting
def format_sse_event(event_type: str, data: dict) -> str:
    try:
        return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
    except Exception as e:
        logger.error("Failed to format SSE event: %s", str(e))
        raise

# Meeting discussion logic
class MeetingDiscussion:
    def __init__(self, group_id: str, strategy: str, topic: str, message: str):
        self.group_id = group_id
        self.strategy = strategy.lower()
        self.topic = topic
        self.message = message
        self.meeting_id = None
        self.participants = {}
        self.questions = []
        self.discussion_log = []

    async def initialize_meeting(self):
        """Create a meeting and fetch participants."""
        meeting_data = MeetingCreate(group_id=self.group_id, strategy=self.strategy, topic=self.topic)
        result = await create_meeting(meeting_data)
        self.meeting_id = result["meeting_id"]
        logger.info("Meeting created with ID: %s", self.meeting_id)
        
        # Fetch participant data
        try:
            conn = sqlite3.connect("roundtableai.db")
            cursor = conn.cursor()
            cursor.execute("SELECT participant_ids FROM groups WHERE id = ?", (self.group_id,))
            result = cursor.fetchone()
            if not result:
                raise HTTPException(status_code=404, detail=f"Group '{self.group_id}' not found")
            participant_ids = json.loads(result[0])
            
            for pid in participant_ids:
                cursor.execute("SELECT name, persona_description FROM participants WHERE id = ?", (pid,))
                data = cursor.fetchone()
                if not data:
                    raise HTTPException(status_code=404, detail=f"Participant '{pid}' not found")
                self.participants[pid] = {"name": data[0], "persona_description": data[1]}
            conn.close()
        except Exception as e:
            logger.error("Error fetching participants: %s", str(e))
            raise

    def generate_questions(self, llm_client):
        """Generate 3 relevant questions based on the topic."""
        prompt = (
            f"Generate exactly 3 concise, relevant questions for a discussion on '{self.topic}'. Do not respond with any other details\n"
            f"List them as:\n1. Question 1\n2. Question 2\n3. Question 3"
        )
        messages = [{"role": "system", "content": prompt}]
        response, _ = llm_client.send_request(messages)  # Unpack tuple, ignore token stats
        content = response.strip().split("\n")
        self.questions = [line.strip()[3:] for line in content if line.strip()]
        if len(self.questions) != 3:
            raise HTTPException(status_code=500, detail="Failed to generate exactly 3 questions")
        logger.info("Questions generated: %s", self.questions)

    def ask_question(self, llm_client, participant_id: str, question: str, context: str = None):
        """Ask a question to a participant with concise, conversational response."""
        participant = self.participants[participant_id]
        prompt = (
            f"You are {participant['name']}, a {participant['persona_description']}. "
            f"Respond to this question in a brief, conversational way, as you would in a meeting: '{question}'. "
            f"Keep it concise, to the point, and reflective of your persona. No extra fluff."
        )
        if context:
            prompt += f"\n\nContext from previous answers: {context}"
        messages = [{"role": "system", "content": prompt}, {"role": "user", "content": self.message}]
        response, _ = llm_client.send_request(messages)  # Unpack tuple, ignore token stats
        return response.strip()

    def gauge_opinion_strength(self, llm_client, participant_id: str, question: str):
        """Gauge how strongly a participant feels about a question."""
        participant = self.participants[participant_id]
        prompt = (
            f"You are {participant['name']}, a {participant['persona_description']}. "
            f"For the question: '{question}', do you have an opinion to share? "
            f"If yes, rate how strongly you feel about it (1-10, 10 being strongest). "
            f"Respond with just a number (e.g., '7'). If no opinion, respond '0'."
        )
        messages = [{"role": "system", "content": prompt}, {"role": "user", "content": question}]
        response, _ = llm_client.send_request(messages)  # Unpack tuple, ignore token stats
        try:
            return int(response.strip())
        except ValueError:
            logger.warning("Invalid strength from %s: %s", participant['name'], response)
            return 0

    def synthesize_response(self, llm_client):
        """Synthesize a final response from the discussion log."""
        prompt = (
            f"Based on this discussion log for the topic '{self.topic}' and user message '{self.message}', "
            f"provide a concise summary or conclusion:\n{json.dumps(self.discussion_log, indent=2)}"
        )
        messages = [{"role": "system", "content": prompt}]
        response, _ = llm_client.send_request(messages)  # Unpack tuple, ignore token stats
        return response.strip()

    async def conduct_discussion(self, llm_client):
        """Conduct the discussion based on strategy and yield SSE events."""
        if self.strategy not in ["round robin", "opinionated"]:
            raise HTTPException(status_code=400, detail="Invalid strategy")

        # Generate questions
        self.generate_questions(llm_client)
        yield format_sse_event("questions", {"questions": self.questions})

        # Handle discussion per strategy
        if self.strategy == "round robin":
            context = ""
            for question in self.questions:
                for pid in self.participants:
                    answer = self.ask_question(llm_client, pid, question, context)
                    self.discussion_log.append({
                        "participant": self.participants[pid]["name"],
                        "question": question,
                        "answer": answer
                    })
                    yield format_sse_event("participant_response", {
                        "participant": self.participants[pid]["name"],
                        "question": question,
                        "answer": answer
                    })
                    context += f"{self.participants[pid]['name']}: {answer}\n"
                await asyncio.sleep(0.1)

        elif self.strategy == "opinionated":
            for question in self.questions:
                opinions = {}
                for pid in self.participants:
                    strength = self.gauge_opinion_strength(llm_client, pid, question)
                    opinions[pid] = strength
                
                sorted_participants = sorted(opinions.items(), key=lambda x: x[1], reverse=True)
                context = ""
                for pid, strength in sorted_participants:
                    if strength > 0:
                        answer = self.ask_question(llm_client, pid, question, context)
                        self.discussion_log.append({
                            "participant": self.participants[pid]["name"],
                            "question": question,
                            "answer": answer,
                            "strength": strength
                        })
                        yield format_sse_event("participant_response", {
                            "participant": self.participants[pid]["name"],
                            "question": question,
                            "answer": answer,
                            "strength": strength
                        })
                        context += f"{self.participants[pid]['name']} (Strength {strength}): {answer}\n"
                await asyncio.sleep(0.1)

        # Synthesize final response
        final_response = self.synthesize_response(llm_client)
        yield format_sse_event("final_response", {"response": final_response})
        yield format_sse_event("complete", {})

async def stream_meeting_discussion(group_id: str, strategy: str, message: str):
    """Stream the meeting discussion using SSE (for main.py compatibility)."""
    try:
        # Use topic from message if not separately provided
        topic = message  # Adjust if main.py changes to separate topic field
        chat_message = ChatMessage(group_id=group_id, strategy=strategy, topic=topic, message=message)
        discussion = MeetingDiscussion(chat_message.group_id, chat_message.strategy, chat_message.topic, chat_message.message)
        await discussion.initialize_meeting()
        llm_client = get_llm_client()
        async for event in discussion.conduct_discussion(llm_client):
            yield event
    except HTTPException as e:
        yield format_sse_event("error", {"detail": str(e.detail)})
    except Exception as e:
        logger.error("Unexpected error: %s", str(e))
        yield format_sse_event("error", {"detail": "Internal server error"})