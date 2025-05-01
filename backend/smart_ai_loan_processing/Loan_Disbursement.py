# import os
# import shutil
# from fastapi import APIRouter, HTTPException, UploadFile, File
# from pymongo import MongoClient
# from paddleocr import PaddleOCR
# import cv2
# import numpy as np
# from pathlib import Path
# from dotenv import load_dotenv
# from pydantic import BaseModel

# class DisbursementRequest(BaseModel):
#     amount_to_be_disbursed: float

# # FastAPI app
# router = APIRouter()
# load_dotenv()
# ocr = PaddleOCR()
# # Environment Variables
# MONGO_URI = os.getenv("MONGO_URI")
# UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
# COLLECTION_LOAN_INFO = "loan-info"

# # MongoDB Connection
# client = MongoClient(MONGO_URI)
# db =  client["Dummy_data"]
# loan_info_collection = db[COLLECTION_LOAN_INFO]

# # Initialize PaddleOCR

# def find_pan_file():
#     """Finds the PAN card file in the UPLOAD_FOLDER"""
#     for file in os.listdir(UPLOAD_FOLDER):
#         if "PAN" in file.upper() and file.lower().endswith((".png", ".jpg", ".jpeg", ".pdf")):
#             return os.path.join(UPLOAD_FOLDER, file)
#     return None

# def extract_pan_number(image_path):
#     """Extracts PAN number from the image using PaddleOCR"""
#     img = cv2.imread(image_path)
#     if img is None:
#         raise ValueError("Image could not be loaded")
#     results = ocr.ocr(img)
#     for res in results:
#         for line in res:
#             text = line[1][0]
#             if len(text) == 10 and text.isalnum():  # Simple PAN format check
#                 return text
#     return None

# @router.post("/disburse-loan/")
# async def disburse_loan(request: DisbursementRequest):
#     amount_to_be_disbursed = request.amount_to_be_disbursed
#     # Step 1: Find PAN card file
#     pan_file = find_pan_file()
#     if not pan_file:
#         raise HTTPException(status_code=404, detail="PAN card file not found in uploads folder")
    
#     # Step 2: Extract PAN number using PaddleOCR
#     pan_number = extract_pan_number(pan_file)
#     if not pan_number:
#         raise HTTPException(status_code=400, detail="PAN number could not be extracted")
#     print(f"Extracted PAN: {pan_number}")  # Debugging line
    
#     # Step 3: Find user details from MongoDB (case-insensitive search)
#     user_data = loan_info_collection.find_one({"Pan-card": {"$regex": f"^{pan_number}$", "$options": "i"}})
#     if not user_data:
#         print("No matching PAN found in database")  # Debugging line
#         print("Available data in loan-info collection:")
#         for record in loan_info_collection.find():
#             print(record)  # Print all records for debugging
#         raise HTTPException(status_code=404, detail="User not found in loan-info database")
    
#     applicant_name = user_data.get("applicant_name", "Unknown")
#     application_number = user_data.get("application_number", "Unknown")
#     loan_amount = user_data.get("loan_amount", 0.0)
#     remaining_amount = loan_amount - amount_to_be_disbursed
    
#     return {
#         "message": f"The amount to be disbursed is {amount_to_be_disbursed}",
#         "applicant_name": applicant_name,
#         "application_number": application_number,
#         "loan_amount": loan_amount,
#         "remaining_amount": remaining_amount
#     }


import os
import shutil
from fastapi import APIRouter, HTTPException
from pymongo import MongoClient
from paddleocr import PaddleOCR
import cv2
from dotenv import load_dotenv

# FastAPI app
router = APIRouter()
load_dotenv()
ocr = PaddleOCR()

# Environment Variables
MONGO_URI = os.getenv("MONGO_URI")
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
COLLECTION_LOAN_INFO = "loan-info"

# MongoDB Connection
client = MongoClient(MONGO_URI)
db = client["Dummy_data"]
loan_info_collection = db[COLLECTION_LOAN_INFO]

# Function to find PAN card file
def find_pan_file():
    for file in os.listdir(UPLOAD_FOLDER):
        if "PAN" in file.upper() and file.lower().endswith((".png", ".jpg", ".jpeg", ".pdf")):
            return os.path.join(UPLOAD_FOLDER, file)
    return None

# Function to extract PAN number
def extract_pan_number(image_path):
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError("Image could not be loaded")
    results = ocr.ocr(img)
    for res in results:
        for line in res:
            text = line[1][0]
            if len(text) == 10 and text.isalnum():  # Simple PAN format check
                return text
    return None

@router.post("/disburse-loan/")
async def disburse_loan():
    # Step 1: Find PAN card file
    pan_file = find_pan_file()
    if not pan_file:
        raise HTTPException(status_code=404, detail="PAN card file not found in uploads folder")
    
    # Step 2: Extract PAN number using PaddleOCR
    pan_number = extract_pan_number(pan_file)
    if not pan_number:
        raise HTTPException(status_code=400, detail="PAN number could not be extracted")
    print(f"Extracted PAN: {pan_number}")  # Debugging line
    
    # Step 3: Find user details from MongoDB (case-insensitive search)
    user_data = loan_info_collection.find_one({"Pan-card": {"$regex": f"^{pan_number}$", "$options": "i"}})
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found in loan-info database")
    
    applicant_name = user_data.get("applicant_name", "Unknown")
    application_number = user_data.get("application_number", "Unknown")
    loan_amount = float(user_data.get("loan_amount", 0.0))
    disbursed_amount = float(user_data.get("Disbursed_amount", 0.0))
    remaining_amount = loan_amount - disbursed_amount
    
    # Determine disbursement status
    if disbursed_amount == loan_amount:
        disbursement_status = "Fully Disbursed"
    else:
        disbursement_status = "Partially Disbursed"
    
    return {
        "applicant_name": applicant_name,
        "application_number": application_number,
        "loan_amount": loan_amount,
        "disbursed_amount": disbursed_amount,
        "remaining_amount": remaining_amount,
        "disbursement_status": disbursement_status
    }
