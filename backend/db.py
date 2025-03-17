import sqlite3
import chromadb
from chromadb.config import Settings

# Initialize SQLite database
def init_sqlite_db():
    conn = sqlite3.connect("agents.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS agents (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            persona_description TEXT NOT NULL
        )
    """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS chatrooms (
            id TEXT PRIMARY KEY,
            agent_ids TEXT NOT NULL,  -- Store as JSON string
            topic TEXT
        )
    """
    )
    conn.commit()
    conn.close()

# Initialize ChromaDB client with persistence
chroma_client = chromadb.PersistentClient(path="./chroma_data")

# Ensure the "agents" collection exists
try:
    collection = chroma_client.get_collection(name="agents")
except chromadb.errors.InvalidCollectionException:
    # If it doesn't exist, create it
    collection = chroma_client.create_collection(name="agents")

# Call SQLite initialization on module load
init_sqlite_db()