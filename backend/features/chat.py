import json
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
import asyncio
from logger_config import setup_logger
from features.meeting import Meeting
from features.chat_session import ChatSessionCreate, create_chat_session
from cosmos_db import cosmos_client
from datetime import datetime, timezone
import uuid
from features.llm import get_llm_client

# Set up logger
logger = setup_logger(__name__)


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
        self.chat_session = None
        self.message_history = []  # List to store message history
        self.user_id = meeting.user_id  # Add user_id from meeting

        # Map participants from participant_order
        self.participants = {}
        for order in meeting.participant_order:
            participant = next((p for p in meeting.participants if p["participant_id"] == order.participant_id), None)
            if participant:
                self.participants[participant["participant_id"]] = {
                    "name": participant["name"],
                    "persona_description": participant.get("persona_description", "participant"),
                    "role": participant.get("role", "Team Member"),
                    "weight": order.weight,
                    "order": order.order,
                }
        logger.info("Initialized meeting discussion for user '%s'", self.user_id)

    def ask_question(self, llm_client, participant_id: str, question: str, messages_list=None):
        """Ask a question to a participant with concise, conversational response."""
        participant = self.participants[participant_id]

        # Part 1: System Prompt
        participant_list = [f"{p['name']} ({p['role']})" for p in self.participants.values()]
        system_prompt = (
            f"You are {participant['persona_description']}. "
            f"Your role is {participant['role']}. "
            f"You are participating in a meeting about '{self.topic}'. "
            f"Meeting participants: {', '.join(participant_list)}. "
            f"Keep it concise, to the point, and reflective of your persona. No extra fluff."
            f"Provide response in a conversational manner, as you(human) would in a meeting. "
        )

        # Part 2: Message History
        messages = [{"role": "system", "content": system_prompt}]
        if messages_list:
            messages.extend(messages_list)

        # Part 3: Current Question
        messages.append({"role": "user", "content": f"Please provide a concise response in a conversational manner to this question based on the meeting topic: {question}"})

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

    async def synthesize_response(self, llm_client):
        """Synthesize a final response from the discussion log and store in chat session."""
        # Part 1: System Prompt
        participants_info = []
        for pid, p in self.participants.items():
            participants_info.append(f"{p['name']} ({p['role']}) - Weight: {p['weight']}, Order: {p['order']}")

        system_prompt = (
            f"You are provided with a meeting transcript of a meeting conducted for topic '{self.topic}'. "
            f"\n\nParticipants in the meeting:\n" + "\n".join(participants_info) + "\n\n"
            f"Important Note: Each participant has a weight assigned (1-10) that indicates their expertise and influence level. "
            f"Participants with higher weights should have their contributions valued more heavily in the final analysis.\n\n"
            f"Objective: Understand the meeting discussion and provide a summary that includes:\n"
            f"- All important discussion points, prioritizing input from high-weight participants\n"
            f"- Pros and cons discussed, with emphasis on points raised by more influential participants\n"
            f"- Main arguments and perspectives, weighted by participant expertise\n"
            f"- Key contributions from each participant considering their role, expertise, and assigned weight\n"
            f"Please analyze each participant's input considering their role and weight, giving more emphasis to higher-weighted participants' perspectives."
        )

        # Part 2: Message Log (all as user messages)
        messages = [{"role": "system", "content": system_prompt}]
        for entry in self.discussion_log:
            msg = f"{entry['participant']} responding to '{entry['question']}': {entry['answer']}"
            messages.append({"role": "user", "content": msg})

        # Part 3: Final Request
        messages.append(
            {
                "role": "user",
                "content": (
                    f"Based on the above meeting transcript, please provide a comprehensive summary of the discussion on '{self.topic}'. "
                    f"Consider each participant's weight when analyzing their contributions - participants with higher weights "
                    f"should have their input weighted more heavily in the final analysis. Include the key points made by each "
                    f"participant, their perspectives based on their roles and weights, and synthesize the overall discussion "
                    f"into clear, actionable insights. When highlighting consensus or differences in viewpoints, give more "
                    f"consideration to the opinions of participants with higher weights."
                ),
            }
        )

        # Get response
        response, _ = llm_client.send_request(messages)  # Unpack tuple, ignore token stats
        response = response.strip()

        # Create/update chat session
        if not self.chat_session:
            session_id = str(uuid.uuid4())
            self.chat_session = {"id": session_id, "meeting_id": self.meeting_id, "user_id": self.user_id, "messages": [{"role": "system", "content": system_prompt}], "display_messages": []}

        # Add summary message
        self.chat_session["messages"].append({"role": "assistant", "content": response})
        self.chat_session["display_messages"].append(
            {"role": "system", "content": response, "type": "summary", "name": "Meeting Summary", "step": "final", "timestamp": datetime.now(timezone.utc).isoformat()}
        )

        # Save chat session using cosmos_db client
        await cosmos_client.update_chat_session(self.chat_session)
        return response

    async def conduct_discussion(self, llm_client):
        """Conduct the discussion based on strategy and yield SSE events."""
        if self.strategy not in ["round robin", "opinionated", "chat"]:
            raise HTTPException(status_code=400, detail="Invalid strategy")

        # Initialize chat session
        # Chat container is accessed via cosmos_client methods now
        session_id = str(uuid.uuid4())
        self.chat_session = {"id": session_id, "meeting_id": self.meeting_id, "user_id": self.user_id, "messages": [], "display_messages": []}

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

                    answer = self.ask_question(llm_client, pid, question, self.message_history)
                    # Add to discussion log
                    self.discussion_log.append({"participant": self.participants[pid]["name"], "question": question, "answer": answer})
                    # Add to message history
                    self.message_history.append({"role": "assistant", "content": f"{self.participants[pid]['name']} said \"{answer}\""})
                    # Add to chat session
                    self.chat_session["messages"].append({"role": "assistant", "content": answer})
                    self.chat_session["display_messages"].append(
                        {
                            "role": self.participants[pid]["role"],
                            "content": answer,
                            "type": "participant",
                            "name": self.participants[pid]["name"],
                            "step": f"question_{len(self.questions)}_participant_{pid}",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    )
                    # Save chat session
                    await cosmos_client.update_chat_session(self.chat_session)
                    yield format_sse_event("participant_response", {"participant": self.participants[pid]["name"], "question": question, "answer": answer})
                    await asyncio.sleep(0.1)  # Add delay after each response

        elif self.strategy == "opinionated":
            for question in self.questions:
                opinions = {}
                for pid in self.participants:
                    strength = self.gauge_opinion_strength(llm_client, pid, question)
                    opinions[pid] = strength

                sorted_participants = sorted(opinions.items(), key=lambda x: x[1], reverse=True)
                for pid, strength in sorted_participants:
                    if strength > 0:
                        # Emit next participant event
                        yield format_sse_event("next_participant", {"participant_id": pid, "participant_name": self.participants[pid]["name"]})
                        await asyncio.sleep(0.1)  # Add delay before response

                        answer = self.ask_question(llm_client, pid, question, self.message_history)
                        # Add to discussion log
                        self.discussion_log.append({"participant": self.participants[pid]["name"], "question": question, "answer": answer, "strength": strength})
                        # Add to message history
                        self.message_history.append({"role": "assistant", "content": f"{self.participants[pid]['name']} said \"{answer}\""})
                        # Add to chat session
                        self.chat_session["messages"].append({"role": "assistant", "content": answer})
                        self.chat_session["display_messages"].append(
                            {
                                "role": self.participants[pid]["role"],
                                "content": answer,
                                "type": "participant",
                                "name": self.participants[pid]["name"],
                                "step": f"question_{len(self.questions)}_participant_{pid}_strength_{strength}",
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            }
                        )
                        # Save chat session
                        await cosmos_client.update_chat_session(self.chat_session)
                        yield format_sse_event("participant_response", {"participant": self.participants[pid]["name"], "question": question, "answer": answer, "strength": strength})
                        await asyncio.sleep(0.1)  # Add delay after each response

        # Synthesize final response for round robin and opinionated
        final_response = await self.synthesize_response(llm_client)
        self.chat_session["display_messages"].append(
            {
                "role": "System",
                "content": final_response,
                "type": "final_response",
                "name": "System",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        yield format_sse_event("final_response", {"response": final_response})
        yield format_sse_event("complete", {})

    async def handle_chat_request(self, chat_request: ChatSessionCreate) -> dict:
        """Handle a chat request for the chat strategy."""
        try:
            if self.strategy != "chat" or len(self.participants) != 1:
                raise HTTPException(status_code=400, detail="Invalid meeting: must be chat strategy with exactly one participant")

            # Get or create chat session
            if not chat_request.session_id:
                chat_session = await create_chat_session(chat_request.meeting_id, self.user_id, next(iter(self.participants.keys())))
                session_id = chat_session["id"]
            else:
                try:
                    chat_session = await cosmos_client.get_chat_session(chat_request.session_id, self.user_id)
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
                f"You are {participant_info['persona_description']}. "
                f"Your role is {participant_info['role']}. "
                f"Respond to this question in a brief, conversational way, as you would in a meeting. "
                f"Keep it concise, to the point, and reflective of your persona. No extra fluff."
            )

            # If this is a new chat session, add the system prompt as first message
            if not chat_session["messages"]:
                chat_session["messages"].append({"role": "system", "content": system_prompt})

            # Add user message to history
            chat_session["messages"].append({"role": "user", "content": chat_request.user_message})
            # Add user message to display_messages
            chat_session["display_messages"].append(
                {"role": "user", "content": chat_request.user_message, "type": "user", "name": "You", "step": "", "timestamp": datetime.now(timezone.utc).isoformat()}
            )

            # Get LLM client
            llm_client = await get_llm_client(self.user_id)

            # Send complete history to LLM
            messages = chat_session["messages"]
            response, _ = llm_client.send_request(messages)

            # Add assistant's response to history
            chat_session["messages"].append({"role": "assistant", "content": response})
            # Add assistant's response to display_messages
            chat_session["display_messages"].append(
                {"role": participant_info["role"], "content": response, "type": "participant", "name": participant_info["name"], "step": "", "timestamp": datetime.now(timezone.utc).isoformat()}
            )
            # Get timestamp from last display message
            last_display_message = chat_session["display_messages"][-1]

            # Save updated chat session
            await cosmos_client.update_chat_session(chat_session)

            return {
                "session_id": session_id,
                "response": response,
                "role": participant_info["role"],
                "content": chat_request.user_message,
                "type": "participant",
                "name": participant_info["name"],
                "step": "",
                "timestamp": last_display_message["timestamp"],
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
