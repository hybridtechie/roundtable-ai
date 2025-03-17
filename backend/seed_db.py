import sqlite3
import json
import chromadb
import os
from db import init_sqlite_db

# Initialize ChromaDB client with persistence
chroma_client = chromadb.PersistentClient(path="../chroma_data")

# Function to add default meetings to SQLite and ChromaDB
def add_meetings(meetings, cursor):
    for meeting in meetings:
        # Convert participant_ids list to JSON string for SQLite storage
        participant_ids_json = json.dumps(meeting["participant_ids"])
        group_ids_json = None
        if "group_ids" in meeting and meeting["group_ids"]:
            group_ids_json = json.dumps(meeting["group_ids"])

        # Insert into SQLite
        try:
            cursor.execute(
                """
                INSERT INTO meetings (id, participant_ids, group_ids, context, topic, userId)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (meeting["id"], participant_ids_json, group_ids_json, meeting["context"], None, meeting["userId"]),
            )
        except sqlite3.IntegrityError as e:
            print(f"Meeting '{meeting['id']}' already exists in SQLite, skipping insertion. {e}")
            continue

        print(f"Meeting '{meeting['id']}' added to the database.")

    conn.commit()


def add_participants(participants, cursor):
    for participant in participants:
        try:
            cursor.execute(
                "INSERT INTO participants (id, name, persona_description, role, userId) VALUES (?, ?, ?, ?, ?)",
                (participant["id"], participant["name"], participant["persona_description"], participant["role"], "SuperAdmin"),
            )
        except sqlite3.IntegrityError:
            print(f"Participant '{participant['name']}' with ID '{participant['id']}' already exists in SQLite, skipping insertion.")
            continue

        print(f"Participant '{participant['name']}' with ID '{participant['id']}' added to the database.")

    conn.commit()

def add_groups(groups, cursor):
    for group in groups:
        # Convert participant_ids list to JSON string for SQLite storage
        participant_ids_json = json.dumps(group["participant_ids"])

        # Insert into SQLite
        try:
            cursor.execute(
                """
                INSERT INTO groups (id, name, description, participant_ids, context,  userId)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (group["id"], group["name"], group["description"], participant_ids_json, group["context"], group["userId"]),
            )
        except sqlite3.IntegrityError:
            print(f"Group '{group['id']}' already exists in SQLite, skipping insertion.")
            continue

        print(f"Group '{group['id']}' added to the database.")

    conn.commit()

# Run the script
if __name__ == "__main__":
    init_sqlite_db()
    conn = sqlite3.connect("roundtableai.db")
    cursor = conn.cursor()
    
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    seed_data_path = os.path.join(script_dir, "seed_data.json")
    
    with open(seed_data_path, "r") as file:
        seed_data = json.load(file)
        
    add_participants(seed_data["participants"], cursor)
    add_groups(seed_data["groups"], cursor)
    add_meetings(seed_data["meetings"], cursor)
    
    conn.close()
        
