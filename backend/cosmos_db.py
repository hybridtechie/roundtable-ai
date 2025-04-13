from typing import Dict, List, Optional, Any
from azure.cosmos import CosmosClient, PartitionKey, exceptions
from azure.identity import DefaultAzureCredential
from fastapi import HTTPException
from logger_config import setup_logger
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logger
logger = setup_logger(__name__)

# Azure Cosmos DB configuration
COSMOS_ENDPOINT = "https://nithin-cosmos.documents.azure.com:443/"
COSMOS_KEY = os.getenv("COSMOS_DB_KEY")
DATABASE_NAME = "roundtable"
CONTAINER_NAME = "users"
CHAT_CONTAINER_NAME = "chat_sessions"
VECTOR_DATABASE_NAME = "roundtable-vector"
PARTICIPANT_DOCO_CONTAINER_NAME = "participant_docs"
PARTICIPANT_DOCS_PARTITION_KEY = PartitionKey(path="/participant_id")


class CosmosDBClient:
    def __init__(self, endpoint: str = COSMOS_ENDPOINT, key: Optional[str] = COSMOS_KEY):
        """Initialize Cosmos DB client"""
        try:
            # Check if running in Azure App Service
            # is_app_service = os.getenv('WEBSITE_SITE_NAME') is not None

            # if is_app_service:
            #     # Use managed identity in App Service
            #     logger.info("Running in App Service, using managed identity")
            #     credential = DefaultAzureCredential()
            #     self.client = CosmosClient(endpoint, credential=credential)
            # else:
            # Use cosmos key in local development
            logger.info("Running locally, using cosmos key")
            if not key:
                raise ValueError("COSMOS_DB_KEY environment variable is not set")
            self.client = CosmosClient(endpoint, credential=key)

            # Initialize main database and container
            self.database = self.client.get_database_client(DATABASE_NAME)
            self.container = self.database.get_container_client(CONTAINER_NAME)
            logger.info(f"Successfully initialized Cosmos DB client for database: {DATABASE_NAME} and container: {CONTAINER_NAME}")

            # Initialize vector database and participant docs container
            self.vector_database = self.client.get_database_client(VECTOR_DATABASE_NAME)
            self.participant_docs_container = self.vector_database.get_container_client(PARTICIPANT_DOCO_CONTAINER_NAME)
            logger.info(f"Successfully initialized Cosmos DB client for database: {VECTOR_DATABASE_NAME} and container: {PARTICIPANT_DOCO_CONTAINER_NAME}")

        except exceptions.CosmosHttpResponseError as e:
            if "blocked by your Cosmos DB account firewall settings" in str(e):
                logger.error("Access blocked by firewall. Please add your IP to the allowed list in Azure Portal.")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Cosmos DB client: {str(e)}", exc_info=True)
            raise

    def get_container(self):
        """Get the main container client ('users')"""
        return self.container

    def get_participant_docs_container(self):
        """Get the participant documents container client"""
        return self.participant_docs_container

    async def get_user_data(self, user_id: str) -> Optional[Dict]:
        """Retrieve user data by user ID"""
        try:
            response = self.container.read_item(item=user_id, partition_key=user_id)
            return response
        except exceptions.CosmosResourceNotFoundError:
            logger.warning(f"User {user_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error retrieving user {user_id}: {str(e)}", exc_info=True)
            raise

    async def list_participants(self, user_id: str) -> List[Dict]:
        """List all participants for a user"""
        try:
            user_data = await self.get_user_data(user_id)
            if not user_data:
                return []
            return user_data.get("participants", [])
        except Exception as e:
            logger.error(f"Error listing participants for user {user_id}: {str(e)}", exc_info=True)
            raise

    async def get_participant(self, user_id: str, participant_id: str) -> Optional[Dict]:
        """Get a specific participant by ID"""
        try:
            user_data = await self.get_user_data(user_id)
            if not user_data:
                return None
            participants = user_data.get("participants", [])
            return next((p for p in participants if p.get("id") == participant_id), None)
        except Exception as e:
            logger.error(f"Error getting participant {participant_id}: {str(e)}", exc_info=True)
            raise

    async def update_participant(self, user_id: str, participant_id: str, participant_data: Dict) -> Dict:
        """Update a participant's data"""
        try:
            user_data = await self.get_user_data(user_id)
            if not user_data:
                raise HTTPException(status_code=404, detail=f"User {user_id} not found")

            participants = user_data.get("participants", [])
            participant_idx = next((i for i, p in enumerate(participants) if p.get("id") == participant_id), -1)

            if participant_idx == -1:
                raise HTTPException(status_code=404, detail=f"Participant {participant_id} not found")

            participants[participant_idx] = {**participants[participant_idx], **participant_data}
            user_data["participants"] = participants

            response = self.container.upsert_item(body=user_data)
            logger.info(f"Updated participant {participant_id} for user {user_id}")
            return response
        except Exception as e:
            logger.error(f"Error updating participant {participant_id}: {str(e)}", exc_info=True)
            raise

    async def delete_participant(self, user_id: str, participant_id: str) -> Dict:
        """Delete a participant from the user's data"""
        try:
            user_data = await self.get_user_data(user_id)
            if not user_data:
                raise HTTPException(status_code=404, detail=f"User {user_id} not found")

            participants = user_data.get("participants", [])
            user_data["participants"] = [p for p in participants if p.get("id") != participant_id]

            response = self.container.upsert_item(body=user_data)
            logger.info(f"Deleted participant {participant_id} from user {user_id}")
            return response
        except Exception as e:
            logger.error(f"Error deleting participant {participant_id}: {str(e)}", exc_info=True)
            raise

    async def create_user(self, user_id: str) -> Dict:
        """Create a new user with empty arrays for participants, groups, and meetings"""
        try:
            user_data = {"id": user_id, "participants": [], "groups": [], "meetings": [], "vectors": {}, "llmAccounts": {"default": "", "providers": []}}  # For storing vector data
            response = self.container.create_item(body=user_data)
            logger.info(f"Created new user: {user_id}")
            return response
        except Exception as e:
            logger.error(f"Error creating user {user_id}: {str(e)}", exc_info=True)
            raise

    async def add_participant(self, user_id: str, participant_data: Dict) -> Dict:
        """Add a participant to user's participants array"""
        try:
            user_data = await self.get_user_data(user_id)
            if not user_data:
                user_data = await self.create_user(user_id)

            participants = user_data.get("participants", [])
            participants.append(participant_data)

            user_data["participants"] = participants
            response = self.container.upsert_item(body=user_data)
            logger.info(f"Added participant for user: {user_id}")
            return response
        except Exception as e:
            logger.error(f"Error adding participant for user {user_id}: {str(e)}", exc_info=True)
            raise

    async def add_group(self, user_id: str, group_data: Dict) -> Dict:
        """Add a group to user's groups array"""
        try:
            user_data = await self.get_user_data(user_id)
            if not user_data:
                user_data = await self.create_user(user_id)

            groups = user_data.get("groups", [])
            groups.append(group_data)

            user_data["groups"] = groups
            response = self.container.upsert_item(body=user_data)
            logger.info(f"Added group for user: {user_id}")
            return response
        except Exception as e:
            logger.error(f"Error adding group for user {user_id}: {str(e)}", exc_info=True)
            raise

    async def list_groups(self, user_id: str) -> List[Dict]:
        """List all groups for a user"""
        try:
            user_data = await self.get_user_data(user_id)
            if not user_data:
                return []
            return user_data.get("groups", [])
        except Exception as e:
            logger.error(f"Error listing groups for user {user_id}: {str(e)}", exc_info=True)
            raise

    async def get_group(self, user_id: str, group_id: str) -> Optional[Dict]:
        """Get a specific group by ID"""
        try:
            user_data = await self.get_user_data(user_id)
            if not user_data:
                return None
            groups = user_data.get("groups", [])
            return next((g for g in groups if g.get("id") == group_id), None)
        except Exception as e:
            logger.error(f"Error getting group {group_id}: {str(e)}", exc_info=True)
            raise

    async def update_group(self, user_id: str, group_id: str, group_data: Dict) -> Dict:
        """Update a group's data"""
        try:
            user_data = await self.get_user_data(user_id)
            if not user_data:
                raise HTTPException(status_code=404, detail=f"User {user_id} not found")

            groups = user_data.get("groups", [])
            group_idx = next((i for i, g in enumerate(groups) if g.get("id") == group_id), -1)

            if group_idx == -1:
                raise HTTPException(status_code=404, detail=f"Group {group_id} not found")

            groups[group_idx] = {**groups[group_idx], **group_data}
            user_data["groups"] = groups

            response = self.container.upsert_item(body=user_data)
            logger.info(f"Updated group {group_id} for user {user_id}")
            return response
        except Exception as e:
            logger.error(f"Error updating group {group_id}: {str(e)}", exc_info=True)
            raise

    async def delete_group(self, user_id: str, group_id: str) -> Dict:
        """Delete a group from the user's data"""
        try:
            user_data = await self.get_user_data(user_id)
            if not user_data:
                raise HTTPException(status_code=404, detail=f"User {user_id} not found")

            groups = user_data.get("groups", [])
            user_data["groups"] = [g for g in groups if g.get("id") != group_id]

            response = self.container.upsert_item(body=user_data)
            logger.info(f"Deleted group {group_id} from user {user_id}")
            return response
        except Exception as e:
            logger.error(f"Error deleting group {group_id}: {str(e)}", exc_info=True)
            raise

    async def update_user(self, user_id: str, update_data: Dict) -> Dict:
        """Update user data with provided fields"""
        try:
            user_data = await self.get_user_data(user_id)
            if not user_data:
                raise HTTPException(status_code=404, detail=f"User {user_id} not found")

            # Update only the specified fields
            user_data.update(update_data)

            response = self.container.upsert_item(body=user_data)
            logger.info(f"Updated user data for user: {user_id}")
            return response
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {str(e)}", exc_info=True)
            raise

    async def add_meeting(self, user_id: str, meeting_data: Dict) -> Dict:
        """Add a meeting to user's meetings array"""
        try:
            user_data = await self.get_user_data(user_id)
            if not user_data:
                user_data = await self.create_user(user_id)

            meetings = user_data.get("meetings", [])
            meetings.append(meeting_data)

            user_data["meetings"] = meetings
            response = self.container.upsert_item(body=user_data)
            logger.info(f"Added meeting for user: {user_id}")
            return response
        except Exception as e:
            logger.error(f"Error adding meeting for user {user_id}: {str(e)}", exc_info=True)
            raise

    async def list_meetings(self, user_id: str) -> List[Dict]:
        """List all meetings for a user"""
        try:
            user_data = await self.get_user_data(user_id)
            if not user_data:
                return []
            return user_data.get("meetings", [])
        except Exception as e:
            logger.error(f"Error listing meetings for user {user_id}: {str(e)}", exc_info=True)
            raise

    async def get_meeting(self, user_id: str, meeting_id: str) -> Optional[Dict]:
        """Get a specific meeting by ID"""
        try:
            user_data = await self.get_user_data(user_id)
            if not user_data:
                return None
            meetings = user_data.get("meetings", [])
            return next((m for m in meetings if m.get("id") == meeting_id), None)
        except Exception as e:
            logger.error(f"Error getting meeting {meeting_id}: {str(e)}", exc_info=True)
            raise

    async def update_meeting(self, user_id: str, meeting_id: str, meeting_data: Dict) -> Dict:
        """Update a meeting's data"""
        try:
            user_data = await self.get_user_data(user_id)
            if not user_data:
                raise HTTPException(status_code=404, detail=f"User {user_id} not found")

            meetings = user_data.get("meetings", [])
            meeting_idx = next((i for i, m in enumerate(meetings) if m.get("id") == meeting_id), -1)

            if meeting_idx == -1:
                raise HTTPException(status_code=404, detail=f"Meeting {meeting_id} not found")

            meetings[meeting_idx] = {**meetings[meeting_idx], **meeting_data}
            user_data["meetings"] = meetings

            response = self.container.upsert_item(body=user_data)
            logger.info(f"Updated meeting {meeting_id} for user {user_id}")
            return response
        except Exception as e:
            logger.error(f"Error updating meeting {meeting_id}: {str(e)}", exc_info=True)
            raise

    async def delete_meeting(self, user_id: str, meeting_id: str) -> Dict:
        """Delete a meeting from the user's data"""
        try:
            user_data = await self.get_user_data(user_id)
            if not user_data:
                raise HTTPException(status_code=404, detail=f"User {user_id} not found")

            meetings = user_data.get("meetings", [])
            user_data["meetings"] = [m for m in meetings if m.get("id") != meeting_id]

            response = self.container.upsert_item(body=user_data)
            logger.info(f"Deleted meeting {meeting_id} from user {user_id}")
            return response
        except Exception as e:
            logger.error(f"Error deleting meeting {meeting_id}: {str(e)}", exc_info=True)
            raise

    async def store_vector(self, user_id: str, vector_id: str, vector_data: Dict) -> Dict:
        """Store vector data in the user's document"""
        try:
            user_data = await self.get_user_data(user_id)
            if not user_data:
                user_data = await self.create_user(user_id)

            vectors = user_data.get("vectors", {})
            vectors[vector_id] = vector_data
            user_data["vectors"] = vectors

            response = self.container.upsert_item(body=user_data)
            logger.info(f"Stored vector {vector_id} for user: {user_id}")
            return response
        except Exception as e:
            logger.error(f"Error storing vector for user {user_id}: {str(e)}", exc_info=True)
            raise

    async def test_connection(self) -> bool:
        """Test the connection by querying admin user details"""
        try:
            user_id = "roundtable_ai_admin"
            user_data = await self.get_user_data(user_id)

            if user_data:
                print("\n📊 Admin User Details:")
                print(f"ID: {user_data.get('id', 'N/A')}")
                print(f"Email: {user_data.get('email', 'N/A')}")
                print(f"Display Name: {user_data.get('display_name', 'N/A')}")
                print(f"Participants Count: {len(user_data.get('participants', []))}")
                print(f"Groups Count: {len(user_data.get('groups', []))}")
                print(f"Meetings Count: {len(user_data.get('meetings', []))}")
                return True
            else:
                print(f"❌ Admin user {user_id} not found")
                return False

        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}", exc_info=True)
            return False

    # --- Methods for Participant Documents ---

    async def add_participant_doc_chunk(self, doc_chunk_data: Dict) -> Dict:
        """Add a document chunk to the participant_docs container."""
        try:
            container = self.get_participant_docs_container()
            # Ensure participant_id exists for partition key
            if "participant_id" not in doc_chunk_data:
                logger.error("Missing 'participant_id' in document chunk data.")
                raise ValueError("Document chunk data must include 'participant_id'")

            response = container.upsert_item(body=doc_chunk_data)
            logger.info(f"Successfully added/updated document chunk with id: {doc_chunk_data.get('id')}")
            return response
        except Exception as e:
            logger.error(f"Error adding document chunk {doc_chunk_data.get('id', 'N/A')}: {str(e)}", exc_info=True)
            raise

    async def delete_participant_docs(self, participant_id: str, user_id: str):
        """Delete all document chunks for a specific participant."""
        # Note: user_id might not be strictly needed if participant_id is unique across users,
        # but it's good practice for potential future authorization checks.
        try:
            container = self.get_participant_docs_container()
            query = "SELECT * FROM c WHERE c.participant_id = @participant_id"
            parameters = [{"name": "@participant_id", "value": participant_id}]

            # Query items using the participant_id as the partition key for efficiency
            items_to_delete = list(container.query_items(query=query, parameters=parameters, partition_key=participant_id))

            deleted_count = 0
            for item in items_to_delete:
                container.delete_item(item=item["id"], partition_key=participant_id)
                deleted_count += 1
                logger.debug(f"Deleted document chunk {item['id']} for participant {participant_id}")

            logger.info(f"Deleted {deleted_count} document chunks for participant {participant_id}")

        except Exception as e:
            logger.error(f"Error deleting document chunks for participant {participant_id}: {str(e)}", exc_info=True)
            # Decide if this should raise an exception or just log the error
            # raise # Uncomment if deletion failure should halt operations

    async def vector_search_participant_docs(
        self,
        query_vector: List[float],
        participant_id: Optional[str] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Perform a vector similarity search on participant document chunks.

        Args:
            query_vector: The embedding vector to search against.
            participant_id: Optional participant ID to filter results.
            top_k: The maximum number of results to return.

        Returns:
            A list of matching document chunks with similarity scores.
        """
        try:
            container = self.get_participant_docs_container()
            query = f"SELECT TOP @num_results c.id, c.text_chunk, VectorDistance(c.embeddings, @embedding) AS similarityScore FROM c"
            parameters = [
                {"name": "@num_results", "value": top_k},
                {"name": "@embedding", "value": query_vector},
            ]

            enable_cross_partition = True
            partition_key_param = None

            if participant_id:
                query += " WHERE c.participant_id = @participant_id"
                parameters.append({"name": "@participant_id", "value": participant_id})
                enable_cross_partition = False  # We can target a specific partition
                partition_key_param = participant_id

            query += " ORDER BY VectorDistance(c.embeddings, @embedding)"  # ORDER BY is required for vector search

            logger.debug(f"Executing vector search query: {query} with params: {parameters}")

            results = list(
                container.query_items(query=query, parameters=parameters, enable_cross_partition_query=enable_cross_partition, partition_key=partition_key_param)  # Specify partition key if filtering
            )

            logger.info(f"Vector search found {len(results)} results for top_k={top_k}" + (f" and participant_id={participant_id}" if participant_id else ""))
            return results

        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Cosmos DB HTTP error during vector search: {e}", exc_info=True)
            # Depending on requirements, you might want to return empty list or re-raise
            # For now, let's re-raise to signal a DB issue
            raise HTTPException(status_code=500, detail=f"Database error during vector search: {e.message}")
        except Exception as e:
            logger.error(f"Unexpected error during vector search: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="An unexpected error occurred during vector search.")

    async def get_chat_sessions_container(self):
        """Get the chat sessions container."""
        return self.client.get_database_client(DATABASE_NAME).get_container_client(CHAT_CONTAINER_NAME)

    async def get_user_chat_sessions(self, user_id: str) -> list:
        """Get all chat sessions for a user."""
        try:
            chat_container = await self.get_chat_sessions_container()
            parameters = [{"name": "@user_id", "value": user_id}]
            query = "SELECT * FROM c WHERE c.user_id = @user_id"
            return list(chat_container.query_items(query=query, parameters=parameters, partition_key=user_id))
        except Exception as e:
            logger.error(f"Error getting chat sessions for user {user_id}: {str(e)}")
            raise

    async def get_chat_session(self, session_id: str, user_id: str) -> dict:
        """Get a specific chat session."""
        try:
            chat_container = await self.get_chat_sessions_container()
            return chat_container.read_item(item=session_id, partition_key=user_id)
        except Exception as e:
            logger.error(f"Error getting chat session {session_id}: {str(e)}")
            raise

    async def create_chat_session(self, session_data: dict) -> dict:
        """Create a new chat session."""
        try:
            chat_container = await self.get_chat_sessions_container()
            return chat_container.upsert_item(body=session_data)
        except Exception as e:
            logger.error(f"Error creating chat session: {str(e)}")
            raise

    async def update_chat_session(self, session_data: dict) -> dict:
        """Update a chat session."""
        try:
            chat_container = await self.get_chat_sessions_container()
            return chat_container.upsert_item(body=session_data)
        except Exception as e:
            logger.error(f"Error updating chat session: {str(e)}")
            raise

    async def delete_chat_session(self, session_id: str, user_id: str):
        """Delete a chat session."""
        try:
            chat_container = await self.get_chat_sessions_container()
            chat_container.delete_item(item=session_id, partition_key=user_id)
        except Exception as e:
            logger.error(f"Error deleting chat session {session_id}: {str(e)}")
            raise

    async def delete_meeting_chat_sessions(self, meeting_id: str, user_id: str):
        """Delete all chat sessions for a meeting."""
        try:
            chat_container = await self.get_chat_sessions_container()
            # Use parameterized query
            parameters = [{"name": "@meeting_id", "value": meeting_id}, {"name": "@user_id", "value": user_id}]
            query = "SELECT * FROM c WHERE c.meeting_id = @meeting_id AND c.user_id = @user_id"
            sessions = list(chat_container.query_items(query=query, parameters=parameters, partition_key=user_id))

            for session in sessions:
                chat_container.delete_item(item=session["id"], partition_key=user_id)
                logger.info(f"Deleted chat session {session['id']} for meeting {meeting_id}")
        except Exception as e:
            logger.error(f"Error deleting chat sessions for meeting {meeting_id}: {str(e)}")
            raise

    async def get_user_llm_settings(self, user_id: str) -> dict:
        """Get LLM settings for a user."""
        try:
            parameters = [{"name": "@user_id", "value": user_id}]
            query = "SELECT c.llmAccounts FROM c WHERE c.id = @user_id"
            result = list(self.container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Error getting LLM settings for user {user_id}: {str(e)}")
            raise
        raise


# Initialize single instance of CosmosDB client
try:
    cosmos_client = CosmosDBClient()
    # container = cosmos_client.get_container() # Keep if needed elsewhere
    # participant_docs_container = cosmos_client.get_participant_docs_container() # Keep if needed elsewhere
    logger.info("Successfully initialized Cosmos DB client and containers")
except exceptions.CosmosHttpResponseError as e:
    if "blocked by your Cosmos DB account firewall settings" in str(e):
        logger.error(
            """
        Access blocked by Cosmos DB firewall. To fix this:
        1. Go to Azure Portal -> Cosmos DB Account 'nithin-cosmos'
        2. Navigate to 'Networking' or 'Firewall and virtual networks'
        3. Add your IP address (116.255.44.35) to the allowed list
        """
        )
    raise
except Exception as e:
    logger.error(f"Failed to initialize Cosmos DB container: {str(e)}", exc_info=True)
    raise

if __name__ == "__main__":
    import asyncio

    async def run_test():
        try:
            result = await cosmos_client.test_connection()
            if result:
                print("\n✅ Successfully connected to Cosmos DB!")
            else:
                print("\n❌ Failed to connect to Cosmos DB")
        except Exception as e:
            print(f"\n❌ Error testing connection: {str(e)}")

    asyncio.run(run_test())
