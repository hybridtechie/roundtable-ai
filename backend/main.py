import os
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
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
app = FastAPI(title="Roundtable AI Backend", description="API for managing AI agent discussions, participants, groups, and meetings.", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://wa-roundtableai-frontend-cefzgxbba8c4aqga.australiaeast-01.azurewebsites.net"],  # Local development frontend URL  # Azure deployed frontend URL
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


# --- Custom Exception Handler for CORS ---
# This ensures that even errors raised before the response is processed
# (like in authentication dependencies) still get CORS headers.
@app.exception_handler(HTTPException)
async def cors_aware_exception_handler(request: Request, exc: HTTPException):
    # Get the origin from the request headers
    origin = request.headers.get("origin")

    # Define allowed origins (should match CORSMiddleware config)
    allowed_origins = {"http://localhost:5173", "https://wa-roundtableai-frontend-cefzgxbba8c4aqga.australiaeast-01.azurewebsites.net"}

    # Default response without CORS headers
    response = JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

    # If the origin is allowed, add CORS headers to the error response
    if origin in allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        # You might want to be more specific with methods/headers if needed
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"

    return response


# --- Include Routers ---
# Entity Routers
app.include_router(participant.router)
app.include_router(group.router)
app.include_router(meeting.router)
app.include_router(chat.router)  # Includes /chat-stream and POST /chat-session
app.include_router(chat_session.router)  # Includes CRUD for /chat-session/{id} and GET /chat-sessions
app.include_router(llm.router)
app.include_router(questions.router)
app.include_router(user.router_user)  # Includes /user/me endpoints


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
        host = os.getenv("HOST", "0.0.0.0")  # Default to 0.0.0.0 to be accessible externally
        logger.info("Starting FastAPI server on %s:%d", host, port)
        # Consider adding reload=True for development environments
        # uvicorn.run("main:app", host=host, port=port, reload=True)
        uvicorn.run(app, host=host, port=port)
    except Exception as e:
        logger.critical("Failed to start FastAPI server: %s", str(e), exc_info=True)
        raise  # Re-raise the exception to ensure the failure is visible
