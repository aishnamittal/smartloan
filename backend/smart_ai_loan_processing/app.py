from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse,HTMLResponse
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from fastapi import FastAPI
import risk_assesment_agents
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html
from risk_assesment_agents import RiskAssessmentState  # Import the state model explicitly
from fastapi import FastAPI, APIRouter
from starlette.middleware.cors import CORSMiddleware
from KYC import get_pan_number
import os
from uploads import router as upload
from verification import router as verify
from ocr_service import router as ocr
from KYC import router as kyc
from CardViewer import router as cardviewer
from custonboarding import router as custonboarding
from login import router as login
from Loan_Disbursement import router as disbursement
from starlette.middleware.cors import CORSMiddleware
from KYC import get_pan_number
import os
from pymongo import MongoClient
import smtplib
from email.mime.text import MIMEText
from formautofill import router as formfill 
from docs_backup import router as backup
from authhandler import get_current_user

# Import the risk assessment agents from the separate file
app = FastAPI()
origins = [
    "http://localhost",
    "http://localhost:8000",  # or whatever port your frontend uses
    "*",  # WARNING: Never use this on production
]
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
# MONGO_URI = os.getenv("MONGO_URI")
COLLECTION_LOAN_INFO = os.getenv("COLLECTION_LOAN_INFO")
COLLECTION_EMAIL_PREVIEWS=os.getenv("COLLECTION_EMAIL_PREVIEWS")
COLLECTION_LOAN_STATE=os.getenv("COLLECTION_LOAN_STATE")
COLLECTION_LOGIN=os.getenv("COLLECTION_LOGIN")
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["Dummy_data"]  # Database name
loan_collection = db["loan-info"]
login_collection=db["login"]
credit_collection = db["credit_score_info"]

state_collection = db[COLLECTION_LOAN_STATE]
# Add middleware to the FastAPI app, NOT the router
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific origin for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],  # ✅ Allow all headers, including 'X-UUID'
)

# Include the upload and verification routes
app.include_router(login)
app.include_router(upload)
app.include_router(verify)
app.include_router(ocr)
app.include_router(kyc)
app.include_router(disbursement)
app.include_router(custonboarding)
app.include_router(formfill)
app.include_router(cardviewer)
app.include_router(backup)

app.mount("/static", StaticFiles(directory=r"C:\Users\aishn\Desktop\smartloanfinal\FRONTEND-main\ey-login\public"), name="static")


def get_latest_file():
    """
    Automatically fetch the latest file from the 'uploads' folder.
    """
    try:
        files = [os.path.join(UPLOAD_FOLDER, f) for f in os.listdir(UPLOAD_FOLDER) if f.startswith("PAN") and f.lower().endswith(('.png', '.jpg', '.jpeg', '.pdf'))]
        if not files:
            raise FileNotFoundError("No valid PAN card files found in the uploads folder.")
        latest_file = max(files, key=os.path.getctime)  # Get the most recently added file
        return latest_file
    except Exception as e:
        raise FileNotFoundError(f"Error fetching file: {e}")

class LoanApplication(BaseModel):
    loanApplicationNumber: str
    stage: str
    status: Optional[str] = "pending"
    completeStatus: Optional[str] = "incomplete"
    
@app.get("/api/profile")
def get_profile(username: str = Depends(get_current_user)):
    user = login_collection.find_one({"username": username})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "name": user.get("name","Unkown"),
        "email": user.get("email", username),  # fallback to username
        "phone": user.get("phone_no", "N/A")
    }
@app.post("/api/loan-state")
def create_loan_application(loan: LoanApplication):
    print("Received loan application:", loan.dict())  # Debug print

    if state_collection.find_one({"loanApplicationNumber": loan.loanApplicationNumber}):
        raise HTTPException(status_code=400, detail="Loan application already exists")
    
    state_collection.insert_one(loan.dict())
    
    print("Loan successfully inserted!")  # Debug print
    return {"message": "Loan application created successfully"}


# ✅ Fetch All Loan Applications
@app.get("/api/loan-state")
def get_loan_applications():
    loans = list(state_collection.find({}, {"_id": 0}))  # Exclude `_id` field
    return loans

# # ✅ Update Loan Stage
# @app.put("/api/loan-state/{loan_id}")
# def update_loan_stage(loan_id: str,  new_stage: str):
#     result = state_collection.update_one(
#         {"loanApplicationNumber": loan_id},
#         {"$set": {"stage": new_stage}}
#     )
    
#     if result.matched_count == 0:
#         raise HTTPException(status_code=404, detail="Loan not found")
    
#     return {"message": "Loan stage updated successfully"}

@app.put("/api/loan-state/{loan_id}")
def update_loan_stage(
    loan_id: str,
    new_stage: str,
    status: Optional[str] = None,
    completeStatus: Optional[str]=None
):
    update_data = {"stage": new_stage}
    
    if status:
        update_data["status"] = status
    if completeStatus:
        update_data["completeStatus"] = completeStatus

    result = state_collection.update_one(
        {"loanApplicationNumber": loan_id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Loan not found")

    return {"message": "Loan stage/status updated successfully"}


@app.get("/risk-assessment/")
async def risk_assessment():
    """
    Complete loan risk assessment with email preview.
    """
    try:
        file_path = get_latest_file()
        pan_card = get_pan_number(file_path)
        if not pan_card:
            raise HTTPException(status_code=400, detail="No valid PAN number found in the document.")

        # 1. Fetch Customer Data
        customer_data = risk_assesment_agents.fetch_customer_data(pan_card)

        # 2. Run Risk Assessment Graph
        risk_graph = risk_assesment_agents.RiskAssessmentGraph()
        final_state = risk_graph.run(customer_data)

        # 3. Print Report
        risk_assesment_agents.print_final_report(final_state)
        print(f"🔎 Final state output: {final_state}")

        # 4. Determine loan status and return email preview if applicable
        if final_state.get("loan_eligibility") == "Rejected":
            print("❌ Loan Rejected. Generating email preview...")
            email_data = risk_assesment_agents.send_rejection_email(final_state)

        elif final_state.get("loan_eligibility") == "Approved":
            print("✅ Loan Approved. Generating email preview...")
            email_data = risk_assesment_agents.send_acceptance_email(final_state)

        else:
            print(f"⚠ Unknown loan eligibility status for PAN {pan_card}")
            return JSONResponse(status_code=200, content={"message": "Unknown loan eligibility result."})

        # Ensure email content exists
        if not email_data or not email_data.get("email_content"):
            print("⚠ No email content generated!")
            return JSONResponse(status_code=200, content={"error": "Failed to generate email content."})
        loan_score = risk_assesment_agents.calculate_loan_score(final_state)

        response_payload = {
            "loan_status": final_state,
            "loan_score": loan_score,
            "email_content": email_data.get("email_content", "No email content available."),
            "pan_card": pan_card
        }

        print("📤 Final API response:", response_payload)
        return JSONResponse(status_code=200, content=response_payload)

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"Error during assessment: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
        
    
@app.get("/dropdown")
async def dropdown():
    try:
        file_path = get_latest_file()
        pan_card = get_pan_number(file_path)
        if not pan_card:
            raise HTTPException(status_code=400, detail="No valid PAN number found in the document.")
        
        loan_info = loan_collection.find_one({"Pan-card": pan_card}, {"_id": 0})
        credit_info = credit_collection.find_one({"Pan-card": pan_card}, {"_id": 0})

        if not loan_info or not credit_info:
            raise HTTPException(status_code=404, detail="Customer data not found")

        return {
            "credit_score": credit_info.get("Credit_Score"),
            "Net_Monthly_Income": credit_info.get("Net_Monthly_Income"),
            "salary_slip_verified": loan_info.get("salary_slip_verified"),
            "loan_amount": loan_info.get("loan_amount"),
            "loan_type": loan_info.get("loan_type"),
            "delinquency_history": credit_info.get("num_times_delinquent")
        }

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"Error during assessment: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/send-email")
async def send_email(request: Request):
    """Send the edited email received from the frontend."""

    try:
        data = await request.json()  # Read JSON data from request body
        subject = data.get("subject", "Loan Application Update")  # Default subject if missing
        email_content = data.get("email_content", "Your loan application status has been updated.")

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"❌ Invalid request format: {str(e)}")

    # 🔹 Fetch PAN number from the latest file
    file_path = get_latest_file()
    pan_card = get_pan_number(file_path)

    # 🔹 Retrieve Customer Email from MongoDB
    customer = loan_collection.find_one({"Pan-card": pan_card})
    if not customer or "Email" not in customer:
        raise HTTPException(status_code=404, detail="No email found for the given PAN card.")

    customer_email = customer["Email"]

    # 🔹 SMTP Configuration
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    email_content = email_content.replace("\n", "<br>")  

# Wrap content in an HTML body to ensure proper formatting
    email_html = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        p {{ margin-bottom: 10px; }}
    </style>
</head>
<body>
    {email_content}
</body>
</html>
"""

    # 🔹 Prepare Email
    msg = MIMEText(email_html, "html")  # HTML formatted email
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = customer_email

    try:
        # Send Email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, customer_email, msg.as_string())
        server.quit()

        return {"message": f"✅ Email sent successfully to {customer_email}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ Failed to send email: {str(e)}")

@app.put("/api/loan-complete-status/{loan_id}")
def update_loan_completion_status(loan_id: str, completeStatus: str = "Completed"):
    result = state_collection.update_one(
        {"loanApplicationNumber": loan_id},
        {"$set": {"completeStatus": completeStatus}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Loan not found")
    
    return {"message": "Loan completion status updated successfully"}


@app.get("/")
def home():
    return {"message": "Welcome to the FastAPI File Uploader"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1",port=8000)

