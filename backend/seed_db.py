import sqlite3
import json
import chromadb
import os
from db import init_sqlite_db
from logger_config import setup_logger

# Set up logger
logger = setup_logger(__name__)

# Initialize ChromaDB client with persistence
try:
    chroma_client = chromadb.PersistentClient(path="../chroma_data")
except Exception as e:
    logger.error("Failed to initialize ChromaDB client: %s", str(e), exc_info=True)
    raise


# Function to add default meetings to SQLite and ChromaDB
def add_meetings(meetings, cursor):
    for meeting in meetings:
        try:
            # Convert participant_ids list to JSON string for SQLite storage
            participant_ids_json = json.dumps(meeting["participant_ids"])
            group_ids_json = None
            if "group_ids" in meeting and meeting["group_ids"]:
                group_ids_json = json.dumps(meeting["group_ids"])

            # Insert into SQLite
            cursor.execute(
                """
                INSERT INTO meetings (id, participant_ids, group_ids, context, topic, userId)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (meeting["id"], participant_ids_json, group_ids_json, meeting["context"], None, meeting["userId"]),
            )
            logger.info("Added meeting '%s' to the database", meeting["id"])

        except sqlite3.IntegrityError as e:
            logger.warning("Meeting '%s' already exists in SQLite, skipping insertion: %s", meeting["id"], str(e))
            continue
        except Exception as e:
            logger.error("Failed to add meeting '%s': %s", meeting["id"], str(e), exc_info=True)
            raise

    conn.commit()
    logger.info("Successfully committed all meeting additions")


def add_participants(participants, cursor):
    for participant in participants:
        try:
            cursor.execute(
                "INSERT INTO participants (id, name, persona_description, role, userId) VALUES (?, ?, ?, ?, ?)",
                (participant["id"], participant["name"], participant["persona_description"], participant["role"], "SuperAdmin"),
            )
            logger.info("Added participant '%s' with ID '%s' to the database", participant["name"], participant["id"])

        except sqlite3.IntegrityError as e:
            logger.warning("Participant '%s' with ID '%s' already exists in SQLite, skipping insertion", participant["name"], participant["id"])
            continue
        except Exception as e:
            logger.error("Failed to add participant '%s': %s", participant["name"], str(e), exc_info=True)
            raise

    conn.commit()
    logger.info("Successfully committed all participant additions")


def add_groups(groups, cursor):
    for group in groups:
        try:
            # Convert participant_ids list to JSON string for SQLite storage
            participant_ids_json = json.dumps(group["participant_ids"])

            # Insert into SQLite
            cursor.execute(
                """
                INSERT INTO groups (id, name, description, participant_ids, context, userId)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (group["id"], group["name"], group["description"], participant_ids_json, group["context"], group["userId"]),
            )
            logger.info("Added group '%s' to the database", group["id"])

        except sqlite3.IntegrityError as e:
            logger.warning("Group '%s' already exists in SQLite, skipping insertion", group["id"])
            continue
        except Exception as e:
            logger.error("Failed to add group '%s': %s", group["id"], str(e), exc_info=True)
            raise

    conn.commit()
    logger.info("Successfully committed all group additions")


# Run the script
if __name__ == "__main__":
    try:
        logger.info("Starting database seeding process...")
        init_sqlite_db()

        conn = sqlite3.connect("roundtableai.db")
        cursor = conn.cursor()

        # Get the directory where the script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        seed_data_path = os.path.join(script_dir, "seed_data.json")

        try:
            with open(seed_data_path, "r") as file:
                seed_data = json.load(file)
                logger.info("Successfully loaded seed data from %s", seed_data_path)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse seed data JSON: %s", str(e), exc_info=True)
            raise
        except FileNotFoundError as e:
            logger.error("Seed data file not found at %s", seed_data_path, exc_info=True)
            raise
        except Exception as e:
            logger.error("Failed to read seed data file: %s", str(e), exc_info=True)
            raise

        add_participants(seed_data["participants"], cursor)
        add_groups(seed_data["groups"], cursor)
        add_meetings(seed_data["meetings"], cursor)

        logger.info("Database seeding completed successfully")
    except Exception as e:
        logger.error("Database seeding failed: %s", str(e), exc_info=True)
        raise
    finally:
        if "conn" in locals():
            conn.close()
            logger.info("Database connection closed")
