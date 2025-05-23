from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from typing import Optional
import jwt
from dotenv import load_dotenv
import os
from pydantic import BaseModel
from simple_chat import SimpleAsha

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Asha AI Chatbot",
    description="An intelligent chatbot for career guidance",
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

class TokenData(BaseModel):
    username: Optional[str] = None

class ChatMessage(BaseModel):
    message: str

# Initialize chatbot
chatbot = SimpleAsha(data_dir="data")

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Implement authentication logic here
    # This is a placeholder - you'll need to implement proper authentication
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    with open('index.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@app.post("/chat")
async def chat(message: ChatMessage, token: str = Depends(oauth2_scheme)):
    try:
        response = chatbot.get_response(message.message)
        return JSONResponse(content={"response": response["text"]})
    except Exception as e:
        print(f"Error: {str(e)}")
        return JSONResponse(
            content={"response": "I apologize, but I encountered an error. Please try again."},
            status_code=500
        )

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        os.getenv("JWT_SECRET_KEY"),
        algorithm=os.getenv("JWT_ALGORITHM")
    )
    return encoded_jwt

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)