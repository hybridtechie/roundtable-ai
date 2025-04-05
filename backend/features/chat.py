from pydantic import BaseModel
from utils_llm import LLMClient
import os
from dotenv import load_dotenv
import json
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
import asyncio
from logger_config import setup_logger
from features.meeting import MeetingCreate, Meeting, get_meeting
from cosmos_db import cosmos_client
import uuid
# Set up logger
logger = setup_logger(__name__)

# Models for chat endpoints
class ChatSessionCreate(BaseModel):
    meeting_id: str
    user_message: str
    session_id: str = None

# LLM client initialization
async def get_llm_client(user_id: str):
    try:
        # Fetch only LLM account details from cosmos db
        container = cosmos_client.client.get_database_client("roundtable").get_container_client("users")
        query = f"SELECT c.llmAccounts FROM c WHERE c.id = '{user_id}'"
        user_data = list(container.query_items(query=query, enable_cross_partition_query=True))
        
        if not user_data:
            logger.error(f"User {user_id} not found in cosmos db")
            raise HTTPException(status_code=404, detail="User not found")
            
        if not user_data or "llmAccounts" not in user_data[0]:
            logger.error(f"No LLM accounts configured for user {user_id}")
            raise HTTPException(status_code=400, detail="No LLM accounts configured")
            
        # Get default provider details
        llm_accounts = user_data[0]["llmAccounts"]
        default_provider = llm_accounts.get("default")
        if not default_provider:
            logger.error(f"No default LLM provider set for user {user_id}")
            raise HTTPException(status_code=400, detail="No default LLM provider set")
            
        # Find provider details matching default provider
        provider_details = None
        for provider in llm_accounts.get("providers", []):
            if provider["provider"] == default_provider:
                provider_details = provider
                break
                
        if not provider_details:
            logger.error(f"Details for default provider {default_provider} not found")
            raise HTTPException(status_code=400, detail="Default provider details not found")
            
        # Initialize LLM client with provider details
        client = LLMClient(provider_details)
        logger.debug(f"Initialized LLM client with provider: {default_provider}")
        return client
        
    except HTTPException:
        raise
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
    def __init__(self, meeting: Meeting):
        self.group_id = meeting.group_ids[0] if meeting.group_ids else None
        self.strategy = meeting.strategy
        self.topic = meeting.topic
        self.meeting_id = meeting.id
        self.questions = meeting.questions
        self.discussion_log = []
        self.user_id = meeting.user_id
        
        # Map participants from participant_order
        self.participants = {}
        for order in meeting.participant_order:
            participant = next(
                (p for p in meeting.participants if p["participant_id"] == order.participant_id),
                None
            )
            if participant:
                self.participants[participant["participant_id"]] = {
                    "name": participant["name"],
                    "persona_description": participant.get("persona_description", "participant"),
                    "role": participant.get("role", "Team Member"),
                    "weight": order.weight,
                    "order": order.order
                }
        logger.info("Initialized meeting discussion for user '%s'", self.user_id)

    def generate_questions(self, llm_client):
        """Generate 3 relevant questions based on the topic."""
        prompt = (
            f"Generate exactly 3 concise, relevant questions for a discussion on '{self.topic}'. Do not respond with any other details\n" f"List them as:\n1. Question 1\n2. Question 2\n3. Question 3"
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
        messages = [{"role": "system", "content": prompt}, {"role": "user", "content": self.topic}]
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
            logger.warning("Invalid strength from %s: %s", participant["name"], response)
            return 0

    def synthesize_response(self, llm_client):
        """Synthesize a final response from the discussion log."""
        prompt = f"Based on this discussion log for the topic '{self.topic}', " f"provide a concise summary or conclusion:\n{json.dumps(self.discussion_log, indent=2)}"
        messages = [{"role": "system", "content": prompt}]
        response, _ = llm_client.send_request(messages)  # Unpack tuple, ignore token stats
        return response.strip()

    async def conduct_discussion(self, llm_client):
        """Conduct the discussion based on strategy and yield SSE events."""
        if self.strategy not in ["round robin", "opinionated", "chat"]:
            raise HTTPException(status_code=400, detail="Invalid strategy")

        if self.strategy in ["round robin", "opinionated"]:
            yield format_sse_event("questions", {"questions": self.questions})

            # Handle discussion per strategy
        if self.strategy == "round robin":
            context = ""
            for question in self.questions:
                for pid in self.participants:
                    # Emit next participant event
                    yield format_sse_event("next_participant", {"participant_id": pid, "participant_name": self.participants[pid]["name"]})
                    await asyncio.sleep(0.1)  # Add delay before response

                    answer = self.ask_question(llm_client, pid, question, context)
                    self.discussion_log.append({"participant": self.participants[pid]["name"], "question": question, "answer": answer})
                    yield format_sse_event("participant_response", {"participant": self.participants[pid]["name"], "question": question, "answer": answer})
                    await asyncio.sleep(0.1)  # Add delay after each response
                    context += f"{self.participants[pid]['name']}: {answer}\n"

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
                        # Emit next participant event
                        yield format_sse_event("next_participant", {"participant_id": pid, "participant_name": self.participants[pid]["name"]})
                        await asyncio.sleep(0.1)  # Add delay before response

                        answer = self.ask_question(llm_client, pid, question, context)
                        self.discussion_log.append({"participant": self.participants[pid]["name"], "question": question, "answer": answer, "strength": strength})
                        yield format_sse_event("participant_response", {"participant": self.participants[pid]["name"], "question": question, "answer": answer, "strength": strength})
                        await asyncio.sleep(0.1)  # Add delay after each response
                        context += f"{self.participants[pid]['name']} (Strength {strength}): {answer}\n"

            # Synthesize final response for round robin and opinionated
            final_response = self.synthesize_response(llm_client)
            yield format_sse_event("final_response", {"response": final_response})
            yield format_sse_event("complete", {})

    async def handle_chat_request(self, chat_request: ChatSessionCreate) -> dict:
        """Handle a chat request for the chat strategy."""
        try:
            if self.strategy != "chat" or len(self.participants) != 1:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid meeting: must be chat strategy with exactly one participant"
                )
                
            # Get chat sessions container
            chat_container = cosmos_client.client.get_database_client("roundtable").get_container_client("chat_sessions")
            
            # If no session_id, create a new chat session
            if not chat_request.session_id:
                session_id = str(uuid.uuid4())
                chat_session = {
                    "id": session_id,
                    "meeting_id": chat_request.meeting_id,
                    "messages": [],
                    "participant_id": next(iter(self.participants.keys()))  # Get the only participant's ID
                }
                chat_container.upsert_item(body=chat_session)
            else:
                # Get existing chat session
                try:
                    chat_session = chat_container.read_item(
                        item=chat_request.session_id,
                        partition_key=chat_request.meeting_id
                    )
                    session_id = chat_request.session_id
                except Exception as e:
                    logger.error(f"Error retrieving chat session: {str(e)}")
                    raise HTTPException(status_code=404, detail="Chat session not found")

            # Get participant details
            participant_id = next(iter(self.participants.keys()))
            participant_info = self.participants[participant_id]

            # Get full participant details for context
            participant = await cosmos_client.get_participant(self.user_id, participant_id)
            if not participant:
                raise HTTPException(status_code=404, detail="Participant not found")

            # Create system prompt from participant details
            system_prompt = (
                f"You are {participant_info['name']}, {participant_info['persona_description']}. "
                f"Your role is {participant_info['role']}. "
                f"Context for your responses: {participant['context']}"
            )

            # If this is a new chat session, add the system prompt as first message
            if not chat_session["messages"]:
                chat_session["messages"].append({
                    "role": "system",
                    "content": system_prompt
                })

            # Add user message to history
            chat_session["messages"].append({
                "role": "user",
                "content": chat_request.user_message
            })

            # Get LLM client
            llm_client = await get_llm_client(self.user_id)

            # Send complete history to LLM
            messages = chat_session["messages"]
            response, _ = llm_client.send_request(messages)

            # Add assistant's response to history
            chat_session["messages"].append({
                "role": "assistant",
                "content": response
            })

            # Save updated chat session
            chat_container.upsert_item(body=chat_session)

            return {
                "session_id": session_id,
                "response": response
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error handling chat request: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

async def stream_meeting_discussion(meeting: Meeting):
    """Stream the meeting discussion using SSE."""
    try:
        discussion = MeetingDiscussion(meeting)
        llm_client = await get_llm_client(meeting.user_id)
        async for event in discussion.conduct_discussion(llm_client):
            yield event
    except HTTPException as e:
        yield format_sse_event("error", {"detail": str(e.detail)})
    except Exception as e:
        logger.error("Unexpected error: %s", str(e))
        yield format_sse_event("error", {"detail": "Internal server error"})
