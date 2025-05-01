from paddleocr import PaddleOCR
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import shutil
import app
import KYC
# Load .env variables
load_dotenv()

router = APIRouter()

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "Dummy_data")
COLLECTION_CREDIT = os.getenv("COLLECTION_CREDIT_SCORE")
COLLECTION_LOAN = os.getenv("COLLECTION_LOAN_INFO")

client = MongoClient(MONGO_URI)
db = client["Dummy_data"]
credit_collection = db["credit_score_info"]
loan_collection = db["loan-info"]

# PaddleOCR setup
ocr = PaddleOCR(use_angle_cls=True, lang='en')

UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@router.get("/autofill/")
async def autofill_from_latest_upload():
    # 1. Get the latest uploaded image file
    file_path = app.get_latest_file()  # Make sure this returns the correct path
    
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="No uploaded PAN image found.")

    # 2. Extract PAN number from the image using your KYC module
    pan_number = KYC.get_pan_number(file_path)

    if not pan_number:
        raise HTTPException(status_code=400, detail="PAN number could not be extracted from the latest image.")
    print(pan_number)
    print(f"PAN Number (normalized): {pan_number}")
    credit_info = credit_collection.find_one({"Pan-card": pan_number})
    loan_info = loan_collection.find_one({"Pan-card": pan_number})
    print("Credit Info from DB:", credit_info)
    print("Loan Info from DB:", loan_info)


    if not credit_info or not loan_info:
        raise HTTPException(status_code=404, detail="No matching data found for extracted PAN.")

    autofill_data = {
        "Name": credit_info.get("Name"),
        "pan_number": credit_info.get("Pan-card"),
        "aadhar_number": credit_info.get("Aadhar-card"),
        "disbursement_amount": loan_info.get("Disbursed_amount")
    }
    return JSONResponse(content=autofill_data)
