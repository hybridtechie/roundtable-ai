import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Logger setup
from logger_config import setup_logger

# Import Routers
from routers import participant, group, meeting, chat, chat_session, llm, questions, user

# Set up logger
logger = setup_logger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Roundtable AI Backend",
    description="API for managing AI agent discussions, participants, groups, and meetings.",
    version="0.1.0"
)

# Add CORS middleware
# Define allowed origins based on environment or configuration
allowed_origins = [
    "http://localhost:5173", # Local development frontend
    "https://wa-roundtableai-frontend-cefzgxbba8c4aqga.australiaeast-01.azurewebsites.net", 
]
# Filter out None values in case FRONTEND_URL is not set
allowed_origins = [origin for origin in allowed_origins if origin]

if not allowed_origins:
    logger.warning("No allowed origins configured for CORS. Allowing all origins.")
    # Default to allowing all if none are specified, or handle as an error
    allowed_origins = ["*"] # Be cautious with "*" in production

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all standard methods
    allow_headers=["*"],  # Allows all headers
)

# --- Include Routers ---
# Authentication/Login Router (has no prefix in user.py)
app.include_router(user.router_login)
# Entity Routers
app.include_router(participant.router)
app.include_router(group.router)
app.include_router(meeting.router)
app.include_router(chat.router) # Includes /chat-stream and POST /chat-session
app.include_router(chat_session.router) # Includes CRUD for /chat-session/{id} and GET /chat-sessions
app.include_router(llm.router)
app.include_router(questions.router)
app.include_router(user.router_user) # Includes /user/me endpoints


# --- Health Check Endpoint ---
@app.get("/", tags=["Health Check"])
async def health_check():
    """Basic health check endpoint."""
    try:
        logger.debug("Health check request received")
        return {"status": "Healthy"}
    except Exception as e:
        logger.error("Health check failed unexpectedly: %s", str(e), exc_info=True)
        # Avoid raising HTTPException here if possible, return unhealthy status
        # raise HTTPException(status_code=500, detail="Service unhealthy")
        return {"status": "Unhealthy", "error": str(e)}


# --- Run the App ---
if __name__ == "__main__":
    try:
        port = int(os.getenv("PORT", "8000"))
        host = os.getenv("HOST", "0.0.0.0") # Default to 0.0.0.0 to be accessible externally
        logger.info("Starting FastAPI server on %s:%d", host, port)
        # Consider adding reload=True for development environments
        # uvicorn.run("main:app", host=host, port=port, reload=True)
        uvicorn.run(app, host=host, port=port)
    except Exception as e:
        logger.critical("Failed to start FastAPI server: %s", str(e), exc_info=True)
        raise # Re-raise the exception to ensure the failure is visible
