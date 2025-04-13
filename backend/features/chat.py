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
from features.participant import search_participant_knowledge  # Added import
from features.user import get_me
from typing import List, Dict, Any  # Added for type hinting

# Set up logger
logger = setup_logger(__name__)


# Helper function to fetch and filter knowledge
async def _fetch_and_filter_knowledge(user_id: str, participant_id: str, search_text: str, top_k: int = 3, score_threshold: float = 0.80) -> List[Dict[str, Any]]:
    """Fetches knowledge for a participant and filters by similarity score."""
    knowledge = []
    try:
        knowledge = await search_participant_knowledge(user_id=user_id, participant_id=participant_id, search_text=search_text, top_k=top_k)
        # Filter knowledge based on the score threshold
        filtered_knowledge = [item for item in knowledge if item.get("similarityScore", 0) >= score_threshold]
        logger.info(f"Fetched {len(knowledge)} items, kept {len(filtered_knowledge)} after filtering (threshold: {score_threshold}) for participant {participant_id} based on '{search_text[:30]}...'")
        return filtered_knowledge
    except HTTPException as e:
        logger.warning(f"Could not fetch knowledge for participant {participant_id} (HTTP {e.status_code}): {e.detail}")
    except Exception as e:
        logger.error(f"Unexpected error fetching knowledge for participant {participant_id}: {str(e)}", exc_info=True)
    return []  # Return empty list on error or if no items meet threshold


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
                    "related_knowledge": [],  # Initialize related_knowledge
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
            f"Meeting participants: {', '.join(participant_list)}. " + "\nand a  Moderator: Moderator\n"
            f"Keep it concise, to the point, and reflective of your persona. No extra fluff. Everyone except you in the meeting is human."
            f"Provide response in a conversational manner, as you(human) would in a meeting. You can also refer to others conversationally and agree or disagree with them rather than repeating their points. "
        )

        # Add related knowledge if available
        related_knowledge = participant.get("related_knowledge", [])
        if related_knowledge:
            knowledge_context = "\n\nRelevant background information for you based on your knowledge base. Base your response on the knowledge found below as much as possible.:\n"
            knowledge_context += "\n".join([f"- {item.get('text_chunk', 'N/A')}" for item in related_knowledge])  # Simplified for context length
            # knowledge_context += "\n".join([f"- {item.get('text_chunk', 'N/A')} (Similarity: {item.get('similarityScore', 0):.2f})" for item in related_knowledge])
            system_prompt += knowledge_context

        # Part 2: Message History
        messages = [{"role": "system", "content": system_prompt}]
        if messages_list:
            messages.extend(messages_list)

        # Part 3: Current Question
        moderator_ques = res = json.dumps({"name": "Moderator", "content": f"Please provide a concise response in a conversational manner to this question based on the meeting topic: {question}"})
        messages.append({"role": "user", "content": moderator_ques})
        self.chat_session["messages"].append({"role": "user", "content": moderator_ques})

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
            f"\n\nParticipants in the meeting:\n" + "\n".join(participants_info) + "\nand a  Moderator: Moderator\n"
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

        # Fetch and filter related knowledge for each participant based on the topic
        logger.info(f"Fetching and filtering related knowledge for participants based on topic: '{self.topic}'")
        knowledge_fetch_tasks = []
        participant_ids_for_knowledge = list(self.participants.keys())  # Get IDs before async operations

        for pid in participant_ids_for_knowledge:
            # Define a coroutine using the helper function
            async def fetch_and_assign_knowledge(participant_id):
                filtered_knowledge = await _fetch_and_filter_knowledge(
                    user_id=self.user_id, participant_id=participant_id, search_text=self.topic, top_k=3, score_threshold=0.80  # Explicitly pass threshold
                )
                # Ensure participant still exists in the dictionary before updating
                if participant_id in self.participants:
                    self.participants[participant_id]["related_knowledge"] = filtered_knowledge
                else:
                    logger.warning(f"Participant {participant_id} no longer in participants dict after knowledge fetch.")

            knowledge_fetch_tasks.append(fetch_and_assign_knowledge(pid))

        # Run all knowledge fetch tasks concurrently
        await asyncio.gather(*knowledge_fetch_tasks)
        logger.info("Finished fetching and filtering related knowledge for all participants.")

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
                    res = json.dumps({"name": self.participants[pid]["name"], "content": answer})
                    self.message_history.append({"role": "user", "content": res})
                    # Add to chat session
                    self.chat_session["messages"].append({"role": "user", "content": answer})
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
                logger.error("Invalid meeting: must be chat strategy with exactly one participant")
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

            # Get LLM client (moved earlier)
            llm_client = await get_llm_client(self.user_id)

            # --- Generate Summary for Knowledge Search ---
            search_text = chat_request.user_message  # Default search text
            if chat_session["messages"]:  # Only summarize if there's history
                # Prepare messages for summarization (use existing history before adding current user message)
                messages_for_summary = list(chat_session["messages"])  # Create a copy
                # Add the current user message temporarily for context in summary
                messages_for_summary.append({"role": "user", "content": chat_request.user_message})

                summary_prompt = (
                    "Summarize the following conversation history concisely. Focus specifically on the main topic and the *last user message* provided. "
                    "The summary will be used to search a knowledge base for relevant information to help answer the last user message. "
                    "Output only the summary text."
                )
                summary_messages = [{"role": "system", "content": summary_prompt}]
                # Add conversation history as user messages for the summarizer LLM
                for msg in messages_for_summary:
                    # Simple concatenation, might need refinement based on LLM input format needs
                    summary_messages.append({"role": "user", "content": f"{msg['role']}: {msg['content']}"})

                try:
                    summary_response, _ = llm_client.send_request(summary_messages)
                    search_text = summary_response.strip()
                    logger.info(f"Generated summary for knowledge search: '{search_text[:100]}...'")
                except Exception as e:
                    logger.error(f"Failed to generate summary for knowledge search: {str(e)}. Falling back to user message.")
                    search_text = chat_request.user_message  # Fallback to original message

            # Fetch related knowledge based on the generated summary or user message
            related_knowledge = await _fetch_and_filter_knowledge(
                user_id=self.user_id, participant_id=participant_id, search_text=search_text, top_k=3, score_threshold=0.80  # Use summary or fallback
            )

            user_info = await get_me(self.user_id)

            # Create system prompt from participant details
            system_prompt_base = (
                f"You are {participant_info['persona_description']}. "
                f"Your role is {participant_info['role']}. "
                f"You are chatting with a human user named {user_info['name']}.  "
                f"Respond to the user's message in a brief, conversational way, like in a Slack chat done by your persona."
                f"Keep it concise, to the point, and reflective of your persona. No extra fluff. The user you are chatting with is human."
                f"For the first response, say Hi to the user like Hi {user_info['name']} and introducing yourself briefly along with the response "
            )

            # Add related knowledge to the system prompt if available
            system_prompt = system_prompt_base
            if related_knowledge:
                knowledge_context = "\n\nRelevant background information for you based on your knowledge base. Base your response on the knowledge found below if relevant:\n"
                knowledge_context += "\n".join([f"- {item.get('text_chunk', 'N/A')}" for item in related_knowledge])
                system_prompt += knowledge_context

            # If this is a new chat session or the system prompt has changed, update/add it
            # We check if the first message is a system message and if its content differs
            update_system_prompt = True
            if chat_session["messages"] and chat_session["messages"][0]["role"] == "system":
                if chat_session["messages"][0]["content"] == system_prompt:
                    update_system_prompt = False
                else:
                    # Update existing system prompt
                    chat_session["messages"][0]["content"] = system_prompt
                    update_system_prompt = False  # Already updated

            if update_system_prompt:
                # Prepend the system prompt if it's new or wasn't the first message
                chat_session["messages"].insert(0, {"role": "system", "content": system_prompt})

            # Add user message to history
            chat_session["messages"].append({"role": "user", "content": chat_request.user_message})
            # Add user message to display_messages
            chat_session["display_messages"].append(
                {"role": "user", "content": chat_request.user_message, "type": "user", "name": "You", "step": "", "timestamp": datetime.now(timezone.utc).isoformat()}
            )

            # LLM client already initialized earlier for summary/knowledge search

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
