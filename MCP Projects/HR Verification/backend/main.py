import os
import sqlite3
import json
import base64
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import AsyncOpenAI
from dotenv import load_dotenv
from typing import List, Union, Any

# Load .env from the root directory (one level up from backend/)
root_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(root_env_path)

# Initialize Database
DB_FILE = "candidates.db"
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone_number TEXT,
            email TEXT,
            aadhar_card_image BLOB
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Create images directory
IMAGES_DIR = "images"
os.makedirs(IMAGES_DIR, exist_ok=True)

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

To complete the verification, you need four pieces of information:
1. An image of their Aadhar card (so you can extract their name).
2. Their full name (provided as text).
3. Their email address (provided as text).
4. Their phone number (provided as text).

Instructions:
- If the user hasn't provided all the required information, politely ask them for the specific missing details in a conversational way. Do not proceed with verification until you have all four.
- Once you have the Aadhar card image, their name, their email, and their phone number, perform these validation checks:
  1. Name Match: The name they provided must match the name extracted from their Aadhar card (ignoring case differences).
  2. Phone Number Validation: The phone number must be a valid Indian mobile number.
- If both checks pass, you MUST output ONLY the following JSON structure and no other text:
{"status": "valid", "name": "<extracted_name>", "phone": "<extracted_phone>", "email": "<extracted_email>"}
- If any check fails, politely explain what didn't match (e.g., the name is different, or the phone number is invalid) and ask them to provide the correct information.
- Always speak conversationally. Never just output "valid" or "not_valid" conversational responses."""

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
        
        ai_content = response.choices[0].message.content

        # Intercept valid JSON response
        try:
            # Check if ai_content is a valid JSON and has status "valid"
            # Strip markdown code blocks if the AI accidentally wrapped it
            clean_content = ai_content.strip()
            if clean_content.startswith("```json"):
                clean_content = clean_content[7:-3].strip()
            
            data = json.loads(clean_content)
            if data.get("status") == "valid":
                name = data.get("name")
                phone = data.get("phone")
                email = data.get("email")
                
                # Extract image from user messages
                image_data = None
                for msg in reversed(request.messages):
                    if msg.role == "user" and isinstance(msg.content, list):
                        for item in msg.content:
                            if item.get("type") == "image_url":
                                url = item["image_url"]["url"]
                                if url.startswith("data:image"):
                                    # Extract base64 part
                                    header, base64_str = url.split(",", 1)
                                    image_data = base64.b64decode(base64_str)
                                    break
                        if image_data:
                            break
                
                # Save to database
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO candidates (name, phone_number, email, aadhar_card_image) VALUES (?, ?, ?, ?)",
                    (name, phone, email, image_data)
                )
                conn.commit()
                conn.close()
                
                return {"role": "assistant", "content": "valid"}
        except json.JSONDecodeError:
            pass # Not a JSON string, proceed as normal conversational reply

        return {"role": "assistant", "content": ai_content}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Backend is running!"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("VITE_BACKEND_PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
