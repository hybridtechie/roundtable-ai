import sqlite3
import chromadb
from chromadb.config import Settings
from logger_config import setup_logger

# Set up logger
logger = setup_logger(__name__)


# Initialize SQLite database
def init_sqlite_db():
    try:
        logger.info("Initializing SQLite database...")
        conn = sqlite3.connect("roundtableai.db")
        cursor = conn.cursor()

        # Create tables
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
            CREATE TABLE IF NOT EXISTS groups (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                participant_ids TEXT NOT NULL,  -- Store as JSON string,
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
                group_ids TEXT,  -- Store as JSON string,
                context TEXT,
                topic TEXT,
                userId TEXT NOT NULL DEFAULT 'SuperAdmin'
            )
        """
        )
        conn.commit()
        logger.info("Database tables created successfully")

    except sqlite3.Error as e:
        logger.error("Failed to initialize SQLite database: %s", str(e), exc_info=True)
        raise
    finally:
        if "conn" in locals():
            conn.close()


# Initialize ChromaDB client with persistence
try:
    logger.info("Initializing ChromaDB client...")
    chroma_client = chromadb.PersistentClient(path="./chroma_data")

    # Ensure the "participants" collection exists
    try:
        collection = chroma_client.get_collection(name="roundtableai")
        logger.info("Found existing ChromaDB collection: roundtableai")
    except chromadb.errors.InvalidCollectionException:
        # If it doesn't exist, create it
        collection = chroma_client.create_collection(name="roundtableai")
        logger.info("Created new ChromaDB collection: roundtableai")
except Exception as e:
    logger.error("Failed to initialize ChromaDB client: %s", str(e), exc_info=True)
    raise

# Call SQLite initialization on module load
init_sqlite_db()
