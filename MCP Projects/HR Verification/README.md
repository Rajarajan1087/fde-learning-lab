# HR Verification Agent

This project is an AI-powered HR Verification web application (built with a FastAPI backend and a React/Vite frontend) designed to automate candidate identity checks. 

## Features

1. **Conversational Verification**: It acts as a friendly chat agent that interacts with candidates to collect their Aadhar card image, full name, and phone number.
2. **Automated Validation**: It automatically extracts the name from the Aadhar card image to verify it matches the text name provided, and checks that the phone number is a valid Indian mobile format.
3. **Interactive Feedback**: It guides the user through the process, politely asking for missing details and informing them whether their verification was successful or if there were mismatches.

## How to Start

### Backend
```bash
cd backend
source venv/bin/activate
python main.py
```

### Frontend
```bash
cd frontend
source ~/.nvm/nvm.sh
nvm use 20
npm run dev
```
