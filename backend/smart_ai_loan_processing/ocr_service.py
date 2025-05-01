from fastapi import APIRouter, HTTPException
from paddleocr import PaddleOCR
import os
import requests
import logging
import json
import re
from pymongo import MongoClient

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load values from .env file
INPUT_FOLDER = os.getenv("INPUT_FOLDER", "uploads")
RESULT_FOLDER = os.getenv("RESULT_FOLDER", "results")

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "ocr_db")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "extracted_data")

# Initialize FastAPI router
router = APIRouter()

# Initialize PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang='en')

# Create necessary directories
os.makedirs(INPUT_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# PAN, Aadhaar, Name, and DOB validation regex
PAN_PATTERN = r'^[A-Z]{5}[0-9]{4}[A-Z]$'
AADHAAR_PATTERN = r'\b\d{4}\s?\d{4}\s?\d{4}\b'
DOB_PATTERN = r'\b\d{2}[-./]\d{2}[-./]\d{4}\b'
NAME_PATTERN = r'(?<=Name[:\s])([A-Za-z ]{3,})'

# Function to store extracted data in MongoDB
def save_to_mongodb(data):
    try:
        if data:
            collection.insert_many(data)
            logger.info("Data successfully saved to MongoDB")
    except Exception as e:
        logger.error(f"Failed to save data to MongoDB: {str(e)}")

# Function to perform OCR
def perform_ocr(image_path):
    result = ocr.ocr(image_path)
    logger.debug(f"OCR Result for {image_path}: {result}")
    return result

# Function to process folder
def process_folder():
    extracted_data = []
    image_files = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith((".png", ".jpg", ".jpeg"))]
    if not image_files:
        raise ValueError("No images found in the folder.")

    for image_file in image_files:
        image_path = os.path.join(INPUT_FOLDER, image_file)
        try:
            ocr_result = perform_ocr(image_path)
            detected_texts = " ".join([word_info[1][0] for line in ocr_result for word_info in line])
            logger.debug(f"Detected Texts for {image_file}: {detected_texts}")

            extracted_info = {"Filename": image_file, "Name": "", "DOB": "", "PAN": "", "Aadhar": ""}

            if "pan" in image_file.lower():
                pan_match = re.search(PAN_PATTERN, detected_texts)
                if pan_match:
                    extracted_info["PAN"] = pan_match.group()
            
            if "aadhar" in image_file.lower():
                aadhaar_match = re.search(AADHAAR_PATTERN, detected_texts)
                if aadhaar_match:
                    extracted_info["Aadhar"] = aadhaar_match.group().replace(" ", "")
            
            name_match = re.search(NAME_PATTERN, detected_texts)
            if name_match:
                extracted_info["Name"] = name_match.group().strip()
            
            dob_match = re.search(DOB_PATTERN, detected_texts)
            if dob_match:
                extracted_info["DOB"] = dob_match.group()
            
            extracted_data.append(extracted_info)
        except Exception as e:
            logger.error(f"Error processing {image_file}: {str(e)}")

    if extracted_data:
        save_to_mongodb(extracted_data)
        return {"message": "Processing complete", "extracted_data": extracted_data}
    else:
        return {"message": "No valid PAN, Aadhaar, Name, or DOB data found."}

@router.get("/ocr/")
async def trigger_processing():
    try:
        result = process_folder()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get_extracted_data/")
async def get_extracted_data():
    try:
        data = list(collection.find({}, {"_id": 0}))  # Exclude MongoDB ObjectId from response
        if not data:
            raise HTTPException(status_code=404, detail="No data found in MongoDB")
        return {"extracted_data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
