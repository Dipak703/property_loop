"""
FastAPI Application

REST API server for the Fund Analytics Chatbot.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import uvicorn

from chatbot import FundAnalyticsChatbot
from config import ERROR_MESSAGE, API_KEY_ERROR


# Global chatbot instance (initialized on startup)
chatbot: Optional[FundAnalyticsChatbot] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    global chatbot
    
    # Check for API key
    if not os.getenv('OPENAI_API_KEY'):
        print(f"WARNING: {API_KEY_ERROR}")
        print("API endpoints will not work without OPENAI_API_KEY")
    else:
        try:
            chatbot = FundAnalyticsChatbot()
            print("Chatbot initialized successfully")
            
            # Check if data is loaded
            if chatbot.executor.trades_df is None and chatbot.executor.holdings_df is None:
                print("Warning: Could not load trades.csv or holdings.csv from ./data/")
        except Exception as e:
            print(f"Error initializing chatbot: {e}")
    
    yield



# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Fund Analytics Chatbot API",
    description="LLM-assisted chatbot for analyzing fund data from CSV files",
    version="1.2.0",
    lifespan=lifespan
)


class QuestionRequest(BaseModel):
    """Request model for chat endpoint."""
    question: str


class QuestionResponse(BaseModel):
    """Response model for chat endpoint."""
    answer: str
    success: bool


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML page."""
    try:
        with open("templates/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Error: index.html not found</h1>",
            status_code=404
        )


@app.post("/api/chat", response_model=QuestionResponse)
async def chat(request: QuestionRequest):
    """
    Chat endpoint for asking questions.
    
    Args:
        request: QuestionRequest containing the user's question
        
    Returns:
        QuestionResponse with the answer
    """
    if chatbot is None:
        raise HTTPException(
            status_code=503,
            detail="Chatbot not initialized. Check OPENAI_API_KEY and data files."
        )
    
    if not request.question or not request.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty"
        )
    
    try:
        answer = chatbot.answer_question(request.question.strip())
        
        return QuestionResponse(
            answer=answer,
            success=True
        )
    except Exception as e:
        return QuestionResponse(
            answer=f"Error processing question: {str(e)}",
            success=False
        )


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "chatbot_initialized": chatbot is not None,
        "data_loaded": (
            chatbot is not None and 
            (chatbot.executor.trades_df is not None or chatbot.executor.holdings_df is not None)
        )
    }


@app.get("/api/columns")
async def get_columns():
    """Get available columns from loaded CSV files."""
    if chatbot is None:
        raise HTTPException(
            status_code=503,
            detail="Chatbot not initialized"
        )
    
    try:
        columns = chatbot.executor.get_available_columns()
        return {"columns": columns}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting columns: {str(e)}"
        )


if __name__ == "__main__":
   
    import socket
    
    def is_port_in_use(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    
    # Use port from environment or default to 7001
    port = int(os.getenv("PORT", 7001))
    if is_port_in_use(port):
        print(f"⚠️  Port {port} is already in use!")
        print("Either stop the existing process or use a different port.")
        print(f"\nTo find and stop the process:")
        print(f"  sudo lsof -i :{port}  # or: sudo netstat -tulpn | grep :{port}")
        print(f"  sudo kill -9 <PID>")
        print(f"\nOr use a different port:")
        print(f"  uvicorn api:app --host 0.0.0.0 --port 7000")
        exit(1)
    
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=port,
        reload=True  # Auto-reload on code changes
    )
