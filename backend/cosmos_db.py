from typing import Dict, List, Optional, Any
from azure.cosmos import CosmosClient, PartitionKey, exceptions
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

class CosmosDBClient:
    def __init__(self, endpoint: str = COSMOS_ENDPOINT, key: Optional[str] = COSMOS_KEY):
        """Initialize Cosmos DB client"""
        if not key:
            raise ValueError("COSMOS_DB_KEY environment variable is not set")
            
        try:
            self.client = CosmosClient(endpoint, credential=key)
            self.database = self.client.get_database_client(DATABASE_NAME)
            self.container = self.database.get_container_client(CONTAINER_NAME)
            logger.info(f"Successfully initialized Cosmos DB client for database: {DATABASE_NAME}")
        except exceptions.CosmosHttpResponseError as e:
            if "blocked by your Cosmos DB account firewall settings" in str(e):
                logger.error("Access blocked by firewall. Please add your IP to the allowed list in Azure Portal.")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Cosmos DB client: {str(e)}", exc_info=True)
            raise

    def get_container(self):
        """Get the container client for direct operations"""
        return self.container

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

    async def create_user(self, user_id: str) -> Dict:
        """Create a new user with empty arrays for participants, groups, and meetings"""
        try:
            user_data = {
                "id": user_id,
                "participants": [],
                "groups": [],
                "meetings": [],
                "vectors": {}  # For storing vector data
            }
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
            
            participants = user_data.get('participants', [])
            participants.append(participant_data)
            
            user_data['participants'] = participants
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
            
            groups = user_data.get('groups', [])
            groups.append(group_data)
            
            user_data['groups'] = groups
            response = self.container.upsert_item(body=user_data)
            logger.info(f"Added group for user: {user_id}")
            return response
        except Exception as e:
            logger.error(f"Error adding group for user {user_id}: {str(e)}", exc_info=True)
            raise

    async def add_meeting(self, user_id: str, meeting_data: Dict) -> Dict:
        """Add a meeting to user's meetings array"""
        try:
            user_data = await self.get_user_data(user_id)
            if not user_data:
                user_data = await self.create_user(user_id)
            
            meetings = user_data.get('meetings', [])
            meetings.append(meeting_data)
            
            user_data['meetings'] = meetings
            response = self.container.upsert_item(body=user_data)
            logger.info(f"Added meeting for user: {user_id}")
            return response
        except Exception as e:
            logger.error(f"Error adding meeting for user {user_id}: {str(e)}", exc_info=True)
            raise

    async def store_vector(self, user_id: str, vector_id: str, vector_data: Dict) -> Dict:
        """Store vector data in the user's document"""
        try:
            user_data = await self.get_user_data(user_id)
            if not user_data:
                user_data = await self.create_user(user_id)
            
            vectors = user_data.get('vectors', {})
            vectors[vector_id] = vector_data
            user_data['vectors'] = vectors
            
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

# Initialize single instance of CosmosDB client
try:
    cosmos_client = CosmosDBClient()
    container = cosmos_client.get_container()
    logger.info("Successfully initialized Cosmos DB container")
except exceptions.CosmosHttpResponseError as e:
    if "blocked by your Cosmos DB account firewall settings" in str(e):
        logger.error("""
        Access blocked by Cosmos DB firewall. To fix this:
        1. Go to Azure Portal -> Cosmos DB Account 'nithin-cosmos'
        2. Navigate to 'Networking' or 'Firewall and virtual networks'
        3. Add your IP address (116.255.44.35) to the allowed list
        """)
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