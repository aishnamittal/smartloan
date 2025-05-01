from fastapi import APIRouter, HTTPException, Form
from pymongo import MongoClient
from dotenv import load_dotenv
from authhandler import create_access_token
import os

# Load environment variables from .env
load_dotenv()

# Fetch MongoDB URI from .env
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("MongoDB URI is not set in .env file")

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client["Dummy_data"]  # Database name
login_collection = db["login"]  # Collection name

router = APIRouter()

@router.post("/login/")
async def login(username: str = Form(...), password: str = Form(...)):
    print(f"Received login request: username={username}, password={password}")  # Debugging

    user = login_collection.find_one({"username": username})
    
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect Username")

    if user["password"] != password:
        raise HTTPException(status_code=400, detail="Incorrect Password")
    
    token = create_access_token({"sub": username})

    return {
        "access_token": token,
        "token_type": "bearer",
        "message": "Logged in successfully"
    }
