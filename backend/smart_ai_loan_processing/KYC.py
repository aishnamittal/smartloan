from fastapi import APIRouter, HTTPException
from langchain_core.messages import SystemMessage, HumanMessage
from paddleocr import PaddleOCR
import os
import hashlib
import logging
import numpy as np
import re
import pymongo
from dotenv import load_dotenv
from PIL import Image
from langsmith import traceable
from langchain_google_genai import ChatGoogleGenerativeAI  
from fastapi.responses import JSONResponse

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
COLLECTION_CUSTOMER_INFO = os.getenv("COLLECTION_CUSTOMER_INFO", "customer_info")

# LangSmith setup
langsmith_api_key = os.getenv("LANGSMITH_API_KEY")

if not langsmith_api_key:
    raise ValueError("Missing LANGSMITH_API_KEY. Please set it in the .env file.")

os.environ["LANGCHAIN_API_KEY"] = langsmith_api_key

DB_NAME = "Dummy_data"
COLLECTION_NAME = "credit_score_info"
COLLECTION_CUSTOMER_INFO="customer_info"

# Configure logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Initialize PaddleOCR
ocr = PaddleOCR()
OCR_CONFIDENCE_THRESHOLD = 0.85

# Connect to MongoDB
client = pymongo.MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]
customer_info_collection = db[COLLECTION_CUSTOMER_INFO]

router = APIRouter()

# Function to hash extracted text for fraud detection
def hash_text(text):
    return hashlib.sha256(text.encode()).hexdigest()
def find_confidence(ocr_data, target_value):
    """
    Match OCR text value with the actual extracted value to retrieve confidence.
    """
    if not target_value or not ocr_data:
        return None
    for entry in ocr_data:
        if entry["text"].replace(" ", "") == target_value.replace(" ", ""):
            return entry["confidence"]
    return None

# Function to convert file to image
def convert_file_to_image(file_path):
    try:
        image = Image.open(file_path).convert("RGB")
        return np.array(image)
    except Exception as e:
        logger.error(f"Error converting file to image: {str(e)}")
        return None

# Function to extract text from image
def extract_text_from_image(image):
    try:
        results = ocr.ocr(image, cls=True)
        extracted_text = ""
        words_with_confidence = []

        for line in results:
            if line:
                for word_info in line:
                    if isinstance(word_info, list) and len(word_info) > 1:
                        text, confidence = word_info[1]
                        extracted_text += text + " "
                        words_with_confidence.append({"text": text, "confidence": confidence})

        return extracted_text.strip(), words_with_confidence
    except Exception as e:
        logger.error(f"Error extracting OCR info: {str(e)}")
        return "", []

# Function to extract PAN number
def extract_pan_number(text):
    match = re.search(r"[A-Z]{5}[0-9]{4}[A-Z]{1}", text)
    return match.group(0) if match else None

def extract_name_dob_aadhar(text):
    name_match = re.search(r"\b([A-Z][a-z]+\s[A-Z][a-z]+)\b", text)
    dob_match = re.search(r"\b(\d{2}[/-]\d{2}[/-]\d{4})\b", text)
    aadhar_match = re.search(r"\b\d{4}\s?\d{4}\s?\d{4}\b", text)

    return {
        "name": name_match.group(0) if name_match else None,
        "dob": dob_match.group(0) if dob_match else None,
        "aadhar_number": aadhar_match.group(0).replace(" ", "") if aadhar_match else None
    }

# Function to extract Aadhar number
def extract_aadhar_number(text):
    match = re.search(r"\b\d{4}\s?\d{4}\s?\d{4}\b", text)
    return match.group(0).replace(" ", "") if match else None

# Function to fetch KYC details from MongoDB
# def fetch_kyc_details(identifier, doc_type):
#     query = {"Pan-card" if doc_type == "PAN" else "Aadhar-card": identifier}
#     record = collection.find_one(query)
    
#     if doc_type == "Aadhar":
#         identifier = int(identifier)  # Ensure Aadhaar is an integer
#     if record:
#         record["_id"] = str(record["_id"])  # Convert ObjectId to string
    
#     return record
def fetch_kyc_details(identifier, doc_type):
    if doc_type == "Aadhar":
        identifier = int(identifier)  # Ensure Aadhaar is an integer
    
    query = {"Pan-card" if doc_type == "PAN" else "Aadhar-card": identifier}
    logger.info(f"Fetching KYC details with query: {query}")  # Add logging
    
    record = collection.find_one(query)
    
    if record:
        record["_id"] = str(record["_id"])  # Convert ObjectId to string
    else:
        logger.warning(f"No KYC record found for: {identifier}")
    
    return record

# Function to detect fraud using AI Agent (LangChain & LangSmith)
@traceable(run_type="llm")
def detect_fraud(extracted_text, stored_info):
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-1", google_api_key=GEMINI_API_KEY)
        system_message = SystemMessage(content="You are an AI assistant validating KYC documents and detecting fraud.")
        stored_info_json = stored_info or {}
        user_message = HumanMessage(content=f"Extracted OCR text: {extracted_text}\nStored KYC Data: {stored_info_json}\nAnalyze for fraud signs.")
        response = llm.invoke([system_message, user_message])
        return response.content
    except Exception as e:
        logger.error(f"Error in AI fraud reasoning: {str(e)}")
        return "Error in AI analysis"

# Agents interacting to process documents and do fraud detection
@traceable(run_type="chain")
def process_document(file_path):
    logger.info("Starting document processing")
    image = convert_file_to_image(file_path)
    if image is None:
        return {"error": "Invalid image file."}
    
    extracted_text, _ = extract_text_from_image(image)
    extracted_hash = hash_text(extracted_text)  
    
    file_name = os.path.basename(file_path).lower()
    doc_type = "PAN" if "pan" in file_name else "Aadhar" if "aadhar" in file_name else None
    
    if doc_type == "PAN":
        identifier = extract_pan_number(extracted_text)
    elif doc_type == "Aadhar":
        identifier = extract_aadhar_number(extracted_text)
    else:
        return {"error": "Unable to determine document type."}
    
    if not identifier:
        return {"error": f"{doc_type} number not detected."}
    
    stored_info = fetch_kyc_details(identifier, doc_type)
    kyc_verified = "Yes" if stored_info else "No"
    
    # Check hash for fraud detection
    stored_hash = stored_info.get("hashed_text") if stored_info else None
    if kyc_verified == "Yes" or extracted_hash == stored_hash:
        fraud_analysis = "No Fraud Detected"
    else:
        fraud_analysis = detect_fraud(extracted_text, stored_info)

    result = {
        "document_type": doc_type,
        "identifier": identifier,
        "extracted_text": extracted_text,
        "kyc_verified": kyc_verified,
        "fraud_analysis": fraud_analysis
    }
    
    logger.info(f"Document processing completed: {result}")
    try:
        save_data = {
            "document_type": doc_type,
            "identifier": identifier,
            "extracted_text": extracted_text,
            "kyc_verified": kyc_verified,
            "fraud_analysis": fraud_analysis,
            "hash": extracted_hash,
            "file_name": os.path.basename(file_path)
        }
        customer_info_collection.insert_one(save_data)
        logger.info(f"KYC data saved to {COLLECTION_CUSTOMER_INFO} collection.")
    except Exception as e:
        logger.error(f"Error saving KYC data: {str(e)}")
    return result
# 🔹 New function to return only the PAN number
def get_pan_number(file_path):
    """
    Extracts and returns only the PAN number from the document.
    """
    logger.info("Extracting PAN number from document")

    image = convert_file_to_image(file_path)
    if image is None:
        return None  # Return None if image is invalid

    extracted_text, _ = extract_text_from_image(image)
    pan_number = extract_pan_number(extracted_text)

    return pan_number
# FastAPI Endpoint for bulk processing
@router.get("/KYC")
def process_all_documents():
    results = []
    for file_name in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, file_name)
        if os.path.isfile(file_path):
            results.append(process_document(file_path))
    return results
async def kycVerified():
    kyc_verified = True  # Example response from your verification logic
    return {"kyc_verified": kyc_verified}

# @router.get("/kyc-details/")
# async def get_kyc_details_summary():
#     response = {}

#     for file_name in os.listdir(UPLOAD_FOLDER):
#         file_path = os.path.join(UPLOAD_FOLDER, file_name)  

#         if not os.path.isfile(file_path):
#             response[file_name] = {"error": f"No {file_name} file found."}
#             continue

#         image = convert_file_to_image(file_path)
#         if image is None:
#             response[file_name] = {"error": "Invalid image."}
#             continue

#         extracted_text, ocr_data = extract_text_from_image(image)

#         if "PAN" in file_name.upper():
#             pan = extract_pan_number(extracted_text)
#             db_data = fetch_kyc_details(pan, "PAN") if pan else None

#             response[file_name] = {
#                 "pan_number": pan,
#                 "ocr_confidence": ocr_data,
#                 "db_data": db_data
#             }

#         elif "AADHAR" in file_name.upper():
#             extracted_info = extract_name_dob_aadhar(extracted_text)
#             dob = extract_name_dob_aadhar('dob')
#             aadhar_number = extracted_info.get("aadhar_number")
#             db_data = fetch_kyc_details(aadhar_number, "Aadhar") if aadhar_number else None

#             response[file_name] = {
#                 "aadhar_number": aadhar_number,
#                 "name": extracted_info.get("name"),
#                 "dob": extracted_info.get("dob"),
#                 "ocr_confidence": ocr_data,
#                 "db_data": db_data
#             }

#     return JSONResponse(content=response)
@router.get("/kyc-details/")
async def get_kyc_details_summary():
    response = {}

    for file_name in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, file_name)

        if not os.path.isfile(file_path):
            response[file_name] = {"error": f"No {file_name} file found."}
            continue

        image = convert_file_to_image(file_path)
        if image is None:
            response[file_name] = {"error": "Invalid image."}
            continue

        extracted_text, ocr_data = extract_text_from_image(image)

        # Helper to extract NAME and DOB with confidence
        name_value, name_conf = None, None
        dob_value, dob_conf = None, None

        for i, entry in enumerate(ocr_data):
            text = entry['text']
            text_upper = text.upper()
            conf = entry['confidence']

            # Rule 1: If "NAME" in text, grab next token
            if "NAME" in text_upper and i + 1 < len(ocr_data):
                name_value = ocr_data[i + 1]['text']
                name_conf = ocr_data[i + 1]['confidence']

            # Rule 2: fallback — first high confidence all-uppercase text
            elif not name_value and conf > 0.9 and text.isalpha() and text.isupper():
                name_value = text
                name_conf = conf

            # Rule 3: DOB pattern
            dob_match = re.search(r"\b(\d{2}[/-]\d{2}[/-]\d{2,4})\b", text)
            if dob_match:
                raw_dob = dob_match.group(1)
                if len(raw_dob.split("/")[-1]) == 3:  # Fix year like 991
                    dob_value = raw_dob[:-3] + raw_dob[-3:]
                else:
                    dob_value = raw_dob
                dob_conf = conf

        if "PAN" in file_name.upper():
            pan = extract_pan_number(extracted_text)
            db_data = fetch_kyc_details(pan, "PAN") if pan else None
            pan_conf = find_confidence(ocr_data, pan)

            response[file_name] = {
                # "pan_number": pan,
                # "pan_confidence": round((pan_conf or 0) * 100, 2),
                "pan_number": {
                    "value": pan,
                    "confidence": round((pan_conf or 0) * 100, 2)
                },
                "ocr_confidence": ocr_data,
                "db_data": db_data
            }

        elif "AADHAR" in file_name.upper():
            extracted_info = extract_name_dob_aadhar(extracted_text)
            aadhar_number = extracted_info.get("aadhar_number")
            aadhar_conf = find_confidence(ocr_data, aadhar_number)
            db_data = fetch_kyc_details(aadhar_number, "Aadhar") if aadhar_number else None

            response[file_name] = {
                # "aadhar_number": aadhar_number,
                # "aadhar_confidence": round((aadhar_conf or 0) * 100, 2),
                "aadhar_number": {
                    "value": aadhar_number,
                    "confidence": round((aadhar_conf or 0) * 100, 2)
                },
                "name": {
                    "value": name_value,
                    "confidence": round((name_conf or 0) * 100, 2)
                },
                "dob": {
                    "value": dob_value,
                    "confidence": round((dob_conf or 0) * 100, 2)
                },
                "ocr_confidence": ocr_data,
                "db_data": db_data
            }

    return JSONResponse(content=response)
