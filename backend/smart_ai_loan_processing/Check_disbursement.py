# from fastapi import FastAPI
# from fastapi.responses import JSONResponse
# import requests

# app = FastAPI()

# DISBURSE_LOAN_URL = "http://127.0.0.1:8000/disburse-loan/"  # Update with actual URL if different
# JOTFORM_API_KEY = "2b5304b102f35bc49f75dbabcca76770"
# JOTFORM_FORM_ID = "your_jotform_form_id"  # Replace with your actual JotForm form ID

# def get_latest_form_response():
#     """Fetches the latest submitted form response from JotForm"""
#     headers = {"APIKEY": JOTFORM_API_KEY}
#     url = f"https://api.jotform.com/form/{JOTFORM_FORM_ID}/submissions"
#     response = requests.get(url, headers=headers)
    
#     if response.status_code == 200:
#         submissions = response.json().get("content", [])
#         if submissions:
#             latest_submission = submissions[-1]  # Get the latest submission
#             answers = latest_submission.get("answers", {})
#             for key, value in answers.items():
#                 if "amount_to_be_disbursed" in value.get("name", "").lower():
#                     return float(value.get("answer", 0))  # Extract amount
#     return None

# @app.get("/fetch-and-disburse")
# async def fetch_and_disburse():
#     amount_to_be_disbursed = get_latest_form_response()
#     if amount_to_be_disbursed is None:
#         return JSONResponse(content={"error": "No data found in JotForm"}, status_code=404)
    
#     response = requests.post(DISBURSE_LOAN_URL, json={"amount_to_be_disbursed": amount_to_be_disbursed})
#     if response.status_code == 200:
#         return response.json()
#     else:
#         return {"error": "Failed to process loan disbursement", "details": response.json()}






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
        extracted_text = " ".join(
            word_info[1][0] for line in results if line for word_info in line if isinstance(word_info, list) and len(word_info) > 1 and word_info[1][1] >= OCR_CONFIDENCE_THRESHOLD
        )
        return extracted_text.strip()
    except Exception as e:
        logger.error(f"Error extracting text: {str(e)}")
        return ""

# Function to extract PAN number
def extract_pan_number(text):
    match = re.search(r"[A-Z]{5}[0-9]{4}[A-Z]{1}", text)
    return match.group(0) if match else None

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
    
    extracted_text = extract_text_from_image(image)
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
        # Save extracted data to MongoDB
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

    extracted_text = extract_text_from_image(image)
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
