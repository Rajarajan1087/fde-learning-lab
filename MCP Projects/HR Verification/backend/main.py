import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import AsyncOpenAI
from dotenv import load_dotenv
from typing import List, Union, Any

# Load .env from the root directory (one level up from backend/)
root_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(root_env_path)

app = FastAPI()

# Allow frontend to access backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For simplicity in dev, allowing all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    role: str
    content: Union[str, List[Any]]

class ChatRequest(BaseModel):
    messages: List[Message]
    model: str = "google/gemini-3.1-pro-preview"

# Initialize OpenRouter client
# OpenRouter uses the OpenAI SDK format
client = AsyncOpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=os.getenv("OPENROUTER_API_KEY", "dummy_key"),
)

SYSTEM_PROMPT = """You are a friendly, conversational HR Verification Agent. Your task is to verify a candidate's identity and contact details through a natural conversation.

To complete the verification, you need three pieces of information:
1. An image of their Aadhar card (so you can extract their name).
2. Their full name (provided as text).
3. Their phone number (provided as text).

Instructions:
- If the user hasn't provided all the required information, politely ask them for the specific missing details. Do not proceed with verification until you have all three.
- Once you have the Aadhar card image, their name, and their phone number, perform these validation checks:
  1. Name Match: The name they provided must match the name extracted from their Aadhar card (ignoring case differences).
  2. Phone Number Validation: The phone number must be a valid Indian mobile number (optional "+91", "91", or "0" prefix, followed by exactly 10 digits starting with 6, 7, 8, or 9).
- If both checks pass, congratulate them and let them know the verification was successful.
- If any check fails, politely explain what didn't match (e.g., the name is different, or the phone number is invalid) and ask them to provide the correct information.
- Always speak conversationally. Never just output "valid" or "not_valid"."""

@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        if os.getenv("OPENROUTER_API_KEY") is None:
            return {"role": "assistant", "content": "Error: OPENROUTER_API_KEY is not set in backend/.env"}

        # Format messages for the API and prepend the system prompt
        messages_formatted = [{"role": "system", "content": SYSTEM_PROMPT}] + [
            {"role": msg.role, "content": msg.content} for msg in request.messages
        ]

        response = await client.chat.completions.create(
            model=request.model,
            messages=messages_formatted,
            # extra_headers={"HTTP-Referer": "http://localhost:5173", "X-Title": "LocalChat"}
        )
        
        return {"role": "assistant", "content": response.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Backend is running!"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("VITE_BACKEND_PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
