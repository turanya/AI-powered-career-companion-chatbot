from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from typing import Optional
import jwt
from pydantic import BaseModel
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Simple Asha AI Chatbot",
    description="A simplified version of the chatbot for testing",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Models
class Message(BaseModel):
    content: str
    session_id: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

# Simple response templates
RESPONSES = {
    "greeting": "Hello! I'm Asha, your AI assistant. How can I help you today?",
    "job_search": "I can help you find job opportunities. What kind of job are you looking for?",
    "career_help": "I'd be happy to help with career guidance. What specific area would you like advice on?",
    "education": "I can provide information about educational opportunities. What are you interested in learning?",
    "default": "I understand you're asking about {}. Could you please provide more details?"
}

def get_simple_response(message: str) -> str:
    message = message.lower()
    if any(word in message for word in ["hello", "hi", "hey"]):
        return RESPONSES["greeting"]
    elif any(word in message for word in ["job", "work", "career"]):
        return RESPONSES["job_search"]
    elif any(word in message for word in ["learn", "study", "education"]):
        return RESPONSES["education"]
    elif any(word in message for word in ["advice", "help", "guidance"]):
        return RESPONSES["career_help"]
    else:
        return RESPONSES["default"].format(message[:20])

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Simple token generation for testing
    access_token = jwt.encode(
        {"sub": form_data.username, "exp": datetime.utcnow() + timedelta(minutes=30)},
        os.getenv("JWT_SECRET_KEY", "default-secret"),
        algorithm=os.getenv("JWT_ALGORITHM", "HS256")
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/chat")
async def chat(message: Message, token: str = Depends(oauth2_scheme)):
    try:
        response = get_simple_response(message.content)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000) 