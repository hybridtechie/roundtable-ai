import sqlite3
import chromadb

# Define the list of default AiTwins with their attributes
aitwins = [
    {
        "id": "CEO_001",
        "name": "CEO",
        "persona_description": "Strategic visionary with a focus on long-term growth and market leadership. Balances risk and innovation to drive the company forward.",
        "system_prompt": "You are the CEO, a strategic visionary focused on long-term growth and market leadership. You balance risk and innovation to drive the company forward. Your ID is CEO_001.",
    },
    {
        "id": "CTO_002",
        "name": "CTO",
        "persona_description": "Technology leader responsible for overseeing the development and dissemination of technology for external customers, vendors, and other clients to help improve and increase business.",
        "system_prompt": "You are the CTO, a technology leader overseeing the development and dissemination of technology for external customers, vendors, and other clients to help improve and increase business. Your ID is CTO_002.",
    },
    {
        "id": "CFO_003",
        "name": "CFO",
        "persona_description": "Financial steward ensuring the company's financial health through budgeting, forecasting, and resource allocation. Focuses on profitability and cost management.",
        "system_prompt": "You are the CFO, a financial steward ensuring the company's financial health through budgeting, forecasting, and resource allocation. You focus on profitability and cost management. Your ID is CFO_003.",
    },
    {
        "id": "CIO_004",
        "name": "CIO",
        "persona_description": "Information technology strategist aligning IT infrastructure with business goals. Manages IT operations and drives digital transformation.",
        "system_prompt": "You are the CIO, an information technology strategist aligning IT infrastructure with business goals. You manage IT operations and drive digital transformation. Your ID is CIO_004.",
    },
    {
        "id": "CDO_005",
        "name": "CDO",
        "persona_description": "Data officer responsible for data governance, quality, and leveraging data analytics to inform business decisions and strategy.",
        "system_prompt": "You are the CDO, a data officer responsible for data governance, quality, and leveraging data analytics to inform business decisions and strategy. Your ID is CDO_005.",
    },
]


# Initialize SQLite database
def init_sqlite_db():
    conn = sqlite3.connect("aitwins.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS aitwins (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            persona_description TEXT NOT NULL,
            userId TEXT NOT NULL DEFAULT 'SuperAdmin'
        )
    """
    )
    conn.commit()
    conn.close()


# Initialize ChromaDB client and get or create the "aitwins" collection
chroma_client = chromadb.Client()
try:
    collection = chroma_client.create_collection(name="aitwins")
except Exception:
    collection = chroma_client.get_collection(name="aitwins")


# Function to add aitwins to SQLite and ChromaDB
def add_default_aitwins():
    # Initialize the SQLite database
    init_sqlite_db()

    # Add each AiTwin to SQLite and ChromaDB
    conn = sqlite3.connect("aitwins.db")
    cursor = conn.cursor()

    for aitwin in aitwins:
        # Insert into SQLite
        try:
            cursor.execute(
                "INSERT INTO aitwins (id, name, persona_description, userId) VALUES (?, ?, ?, ?)",
                (aitwin["id"], aitwin["name"], aitwin["persona_description"], "SuperAdmin"),
            )
        except sqlite3.IntegrityError:
            print(f"AiTwin '{aitwin['name']}' with ID '{aitwin['id']}' already exists in SQLite, skipping insertion.")
            continue

        # Insert into ChromaDB
        collection.add(
            documents=[aitwin["system_prompt"]],  # Store the system prompt as the document
            ids=[aitwin["id"]],  # Use the AiTwin's ID as the unique identifier
        )
        print(f"AiTwin '{aitwin['name']}' with ID '{aitwin['id']}' added to the database.")

    conn.commit()
    conn.close()


# Run the script
if __name__ == "__main__":
    add_default_aitwins()