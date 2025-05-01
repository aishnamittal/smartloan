import os
import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from dotenv import load_dotenv
from pymongo import MongoClient
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
load_dotenv()

# Configuration settings
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
ALLOWED_EXTENSIONS = set(os.getenv("ALLOWED_EXTENSIONS", "pdf,png,jpg,jpeg").split(","))
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "file_uploads")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "documents")

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

router = APIRouter()
# Ensure upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Allowed file extension checker
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@router.post("/upload/")
async def upload_file(document_type: str = Form(...), file: UploadFile = File(...)):
    valid_document_types = ["PAN", "Aadhar", "Salary-slip", "Loan-Application"]
    
    if document_type not in valid_document_types:
        raise HTTPException(status_code=400, detail="Invalid document type. Choose from: PAN, Aadhar, Salary-slip, Loan-Application")
    
    if not allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="Invalid file type")

    # Get the file extension
    file_extension = file.filename.rsplit(".", 1)[1].lower()
    
    # Filename without timestamp or UUID
    new_filename = f"{document_type}.{file_extension}"
    file_path = os.path.join(UPLOAD_FOLDER, new_filename)
    
    # Save/overwrite file
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    
    # Store document metadata
    document_data = {
        "document_type": document_type,
        "filename": new_filename,
        "filepath": file_path,
        "uploaded_at": datetime.datetime.now()
    }
    collection.insert_one(document_data)
    
    return {"message": "File uploaded successfully", "filepath":file_path}