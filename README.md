# roundtable-ai

## Project Overview
roundtable-ai is a multi-agent system designed to orchestrate discussions among AI agents. It features a high-performance FastAPI backend and a modern React frontend that facilitate real-time chat and collaboration between participants.

## Main Entities
- **Participant**: Represents an individual user or AI agent involved in discussions.
- **Group**: A collection of participants grouped together for collaborative sessions.
- **Meeting**: A scheduled session where participants discuss and collaborate.
- **Chat**: A core real-time messaging system enabling live streaming of discussions. Chat functionality integrates with a Language Learning Model (LLM) to generate discussion questions and assist in conversation flow.

## Chat Functionality
- **Real-time Streaming**: The chat component streams messages in real time, ensuring instant communication.
- **LLM Integration**: Leverages Azure OpenAI for generating questions and guiding the discussion.
- **Error Handling & Performance**: Designed with robust error handling and optimized for high performance even with complex discussions.

## Technology Stack and Tools
- **Backend:** 
  - FastAPI  
  - Python 3.9+  
  - SQLite for persistent storage  
  - ChromaDB for chat context management  
  - Azure OpenAI for LLM integration
- **Frontend:** 
  - React with shadcn-ui components  
  - TypeScript  
  - Vite as the build tool  
  - TailwindCSS for styling

## Setup and Installation
1. **Backend Setup**:
    - Ensure you have Python 3.9+ installed.
    - Install dependencies: `pip install -r backend/requirements.txt`
    - Configure environment variables as needed (e.g., OpenAI API keys).
    - Start the server: `uvicorn backend.main:app --reload`
2. **Frontend Setup**:
    - Navigate to the frontend directory: `cd frontend/agent-swarm`
    - Install dependencies: `npm install`
    - Start the development server: `npm run dev`
  
## Development Guidelines and Future Enhancements
- Follow PEP 8 guidelines for Python and Prettier formatting for TypeScript code.
- Ensure proper logging and error handling throughout the application.
- Future plans include:
  - Persisting chat logs beyond in-memory storage.
  - Enhancing routing and navigation in the frontend.
  - Expanding the LLM integration for more dynamic interactions.

---

Feel free to contribute and raise issues or pull requests for any improvements.
