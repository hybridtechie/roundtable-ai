import sqlite3
import chromadb
from chromadb.config import Settings


# Initialize SQLite database
def init_sqlite_db():
    conn = sqlite3.connect("roundtableai.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS participants (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            persona_description TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'Team Member',
            userId TEXT NOT NULL DEFAULT 'SuperAdmin',
            context TEXT
        )
    """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS meetings (
            id TEXT PRIMARY KEY,
            participant_ids TEXT NOT NULL,  -- Store as JSON string,
            meeting_context TEXT,
            topic TEXT,
            userId TEXT NOT NULL DEFAULT 'SuperAdmin'
        )
    """
    )
    conn.commit()
    conn.close()


# Initialize ChromaDB client with persistence
chroma_client = chromadb.PersistentClient(path="./chroma_data")

# Ensure the "participants" collection exists
try:
    collection = chroma_client.get_collection(name="roundtableai")
except chromadb.errors.InvalidCollectionException:
    # If it doesn't exist, create it
    collection = chroma_client.create_collection(name="roundtableai")

# Call SQLite initialization on module load
init_sqlite_db()
