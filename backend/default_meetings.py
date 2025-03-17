import sqlite3
import json
import chromadb
from db import init_sqlite_db

# Define the list of default meetings with combinations of AiTwins
default_meetings = [
    {
        "id": "MEET_AGB_001",
        "aitwin_ids": ["EA_SECURITY_001", "EA_INTEGRATION_002", "EA_DATA_003", "EA_GENAI_004"],
        "meeting_context": "The Architecture Governance Body consists of Emily Thompson (Enterprise Architect for Security), Michael Nguyen (Enterprise Architect for Integration), Sophia Martinez (Enterprise Architect for Data), and David Kim (Enterprise Architect for Gen AI). Its objective is to oversee and guide AussieBank’s enterprise architecture strategy, ensuring alignment with business goals, regulatory compliance, and technological innovation. The group evaluates architectural decisions, identifies risks, and promotes best practices across security, integration, data, and AI domains.",
        "topic": "TBD",  # Placeholder, as topic is not specified in meeting_context
        "userId": "SuperAdmin"
    },
    {
        "id": "MEET_EXEC_TECH_002",
        "aitwin_ids": ["CTO_005", "CIO_006", "CDO_007"],
        "meeting_context": "The Executive Technology Leadership Team consists of Rachel O’Connor (Chief Technology Officer), Thomas Müller (Chief Information Officer), and Linda Huang (Chief Data Officer). Its objective is to align AussieBank’s technology and data strategies with long-term business objectives, driving innovation while maintaining operational stability and compliance. The group focuses on strategic investments, risk management, and fostering a culture of technological and data-driven excellence.",
        "topic": "TBD",
        "userId": "SuperAdmin"
    },
    {
        "id": "MEET_SEC_DATA_003",
        "aitwin_ids": ["EA_SECURITY_001", "EA_DATA_003", "CDO_007"],
        "meeting_context": "The Security and Data Alignment Group consists of Emily Thompson (Enterprise Architect for Security), Sophia Martinez (Enterprise Architect for Data), and Linda Huang (Chief Data Officer). Its objective is to ensure that AussieBank’s data management and security practices are tightly integrated, safeguarding customer privacy and financial data while enabling data-driven decision-making. The group addresses compliance with privacy laws, assesses risks, and optimizes data and security architectures.",
        "topic": "TBD",
        "userId": "SuperAdmin"
    },
    {
        "id": "MEET_AI_TRANS_004",
        "aitwin_ids": ["EA_GENAI_004", "CTO_005", "EA_INTEGRATION_002"],
        "meeting_context": "The AI and Transformation Working Group consists of David Kim (Enterprise Architect for Gen AI), Rachel O’Connor (Chief Technology Officer), and Michael Nguyen (Enterprise Architect for Integration). Its objective is to accelerate AussieBank’s digital transformation through the strategic use of generative AI and integrated systems. The group explores innovative AI applications, ensures seamless system integration, and evaluates their impact on operational efficiency and customer experience.",
        "topic": "TBD",
        "userId": "SuperAdmin"
    }
]

# Initialize ChromaDB client with persistence
chroma_client = chromadb.PersistentClient(path="./chroma_data")

# Function to add default meetings to SQLite and ChromaDB
def add_default_meetings():
    # Initialize the SQLite database
    init_sqlite_db()

    # Connect to SQLite
    conn = sqlite3.connect("aitwins.db")
    cursor = conn.cursor()

    for meeting in default_meetings:
        # Convert aitwin_ids list to JSON string for SQLite storage
        aitwin_ids_json = json.dumps(meeting["aitwin_ids"])

        # Insert into SQLite
        try:
            cursor.execute(
                """
                INSERT INTO meetings (id, aitwin_ids, meeting_context, topic, userId)
                VALUES (?, ?, ?, ?, ?)
                """,
                (meeting["id"], aitwin_ids_json, meeting["meeting_context"], meeting["topic"], meeting["userId"]),
            )
        except sqlite3.IntegrityError:
            print(f"Meeting '{meeting['id']}' already exists in SQLite, skipping insertion.")
            continue

        print(f"Meeting '{meeting['id']}' added to the database.")

    conn.commit()
    conn.close()

# Run the script
if __name__ == "__main__":
    add_default_meetings()