import os
import smtplib
import logging
import google.generativeai as genai
from pymongo import MongoClient
from datetime import datetime
from fastapi import FastAPI, HTTPException, APIRouter,Depends
from dotenv import load_dotenv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from langchain.tools import Tool
from langchain.agents import AgentExecutor
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import Tool
from KYC import get_pan_number
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import Image, Table, TableStyle
from reportlab.pdfbase.ttfonts import TTFont
from authhandler import get_current_user
import tempfile
import app
import re
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.pagesizes import letter,A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER

# Load environment variables
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
COLLECTION_LOAN_INFO = os.getenv("COLLECTION_LOAN_INFO")
COLLECTION_APPLICANT_DETAILS = os.getenv("COLLECTION_APPLICANT_DETAILS")
STAFF_COLLECTION = os.getenv("STAFF_COLLECTION")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))  # Defaulting to 587 if not provided
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
COMPANYLOGO = os.getenv("COMPANYLOGO")
# Validate API key
if not GEMINI_API_KEY:
    raise ValueError("❌ Missing GEMINI_API_KEY! Please set it in the .env file.")

# Initialize FastAPI app
router = APIRouter()

# MongoDB Connection
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
loan_collection = db[COLLECTION_LOAN_INFO]
applicant_collection = db[COLLECTION_APPLICANT_DETAILS]
staff_collection = db[STAFF_COLLECTION]

# Logging setup
logging.basicConfig(level=logging.INFO)

# Initialize Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# 🚀 **Agent 1: Fetch Customer Details**
def fetch_customer_details(pan_card):
    loan_data = loan_collection.find_one({"Pan-card": pan_card})
    applicant_data = applicant_collection.find_one({"Pan-card": pan_card})
    
    if not loan_data or not applicant_data:
        raise HTTPException(status_code=404, detail="Customer details not found")
    
    return loan_data, applicant_data
from datetime import datetime

def fetch_logged_in_employee(username):
    employee_data = staff_collection.find_one({"email": username})
    if not employee_data:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee_data

def generate_loan_report(loan_data, applicant_data,employee_data):
    today_date = datetime.today().strftime("%d %B, %Y")

    return f"""
    <html>
    <body>
        <p><strong>Dear {applicant_data['Name']},</strong></p>

        <p>We are delighted to welcome you to <strong>{loan_data['bank_address']}</strong>. This report serves as an official confirmation of your loan approval.</p>

        <p>After evaluating your application and supporting documents, we are pleased to offer you a loan under the following terms:</p>

        <h3>Loan Summary</h3>
        <ul>
            <li><strong>Loan Amount:</strong> ₹{loan_data['loan_amount']}</li>
            <li><strong>Interest Rate:</strong> {loan_data['interest_rate']}%</li>
            <li><strong>EMI:</strong> ₹{loan_data['emi']} per month</li>
            <li><strong>Tenure:</strong> {loan_data.get('tenure', 'N/A')} months</li>
        </ul>

        <h3>Applicant Profile</h3>
        <ul>
            <li><strong>Name:</strong> {applicant_data['Name']}</li>
            <li><strong>Credit Score:</strong> {applicant_data['Credit_Score']}</li>
            <li><strong>Net Monthly Income:</strong> ₹{applicant_data['Net_Monthly_Income']}</li>
            <li><strong>Approval Status:</strong> {applicant_data['Approved_Flag']}</li>
        </ul>

        <h3>Bank Information</h3>
        <ul>
            <li><strong>Bank Name:</strong> {loan_data['bank_address']}</li>
            <li><strong>Authorized Signatory:</strong> {employee_data['name']}:CRO(Customer Relationship Officer</li>
        </ul>

        <p>Please find your detailed onboarding and loan summary attached to this message in PDF format.</p>

        <p>For any further communication, kindly use your application number <strong>{loan_data['application_number']}</strong>.</p>

        <p>We’re excited to support your financial journey. Thank you for choosing us.</p>

        <br>
        <p>Warm regards,</p>
        {employee_data['name']}<br>
        <p><strong>Customer Relationship Officer</strong><br>
        {loan_data['bank_address']}<br>
        Date: {today_date}</p>
    </body>
    </html>
    """

# 🚀 **Agent 3: Convert HTML to PDF**

def strip_html_tags(text):
    """
    Strips HTML tags for ReportLab compatibility.
    """
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)
ARIAL_FONT_PATH = r"C:\Windows\Fonts\arial.ttf"
pdfmetrics.registerFont(TTFont("Arial", ARIAL_FONT_PATH))

def generate_pdf(html_content, filename, logo_path=COMPANYLOGO):
    temp_dir = tempfile.gettempdir()
    pdf_path = os.path.join(temp_dir, filename)

    doc = SimpleDocTemplate(pdf_path, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=60, bottomMargin=40)

    styles = getSampleStyleSheet()

    # Paragraph styles using Arial
    body_style = ParagraphStyle(
        name='Body',
        parent=styles['Normal'],
        fontName='Arial',
        fontSize=11,
        leading=16,
        spaceAfter=10
    )

    heading_style = ParagraphStyle(
        name='Heading',
        parent=styles['Heading1'],
        fontName='Arial',
        fontSize=15,
        leading=20,
        spaceAfter=12,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#1F3A93")
    )

    elements = []

    # Logo
    if logo_path and os.path.exists(logo_path):
        logo = Image(logo_path, width=1.5 * inch, height=1.5 * inch)
        logo.hAlign = 'RIGHT'
        elements.append(logo)

    elements.append(Spacer(1, 12))
    elements.append(Paragraph("Loan Onboarding Report", heading_style))
    elements.append(Spacer(1, 20))

    # Parse HTML-like content
    for line in html_content.split("\n"):
        line = line.strip()

        if not line:
            continue

        if "<br>" in line:
            # Add space instead of invalid <br> tags
            elements.append(Spacer(1, 10))
            continue

        if line.startswith("<h3>"):
            title = line.replace("<h3>", "").replace("</h3>", "")
            elements.append(Paragraph(f"<b>{title}</b>", styles['Heading3']))
        elif line.startswith("<p>"):
            text = line.replace("<p>", "").replace("</p>", "")
            elements.append(Paragraph(text, body_style))
        else:
            # Try to render any other line as normal text
            elements.append(Paragraph(line, body_style))

        elements.append(Spacer(1, 6))


    doc.build(elements)
    return pdf_path

# 🚀 **Agent 4: Send Email with PDF**
def send_email(to_email, subject, body, pdf_path):
    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_USER
        msg["To"] = to_email
        msg["Subject"] = subject

        
        # Format the body to preserve line breaks in HTML
        html_body = body.replace('\n', '<br>')
        full_html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6;">
            {html_body}
          </body>
        </html>
        """

        html_part = MIMEText(full_html, "html")
        msg.attach(html_part)


        # Attach the PDF only if pdf_path is provided
        if pdf_path:
            with open(pdf_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(pdf_path)}")
                msg.attach(part)

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, to_email, msg.as_string())

        logging.info(f"✅ Email sent successfully to {to_email}")

    except Exception as e:
        logging.error(f"❌ Error sending email: {e}")
        raise HTTPException(status_code=500, detail="Failed to send email")

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

def generate_loan_recommendation(loan_data, applicant_data,employee_data):
    return f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; padding: 20px;">
        <p><strong>Dear {applicant_data['Name']},</strong></p>

        <p>Greetings from <strong>{loan_data['bank_address']}</strong>!</p>

        <p>We wish to acknowledge receipt of your loan application number <strong>{loan_data['application_number']}</strong> in the name of <strong>{applicant_data['Name']}</strong>. Thank you for choosing <strong>{loan_data['bank_address']}</strong>.</p>
        <p>I, {employee_data['name']} would be your Relationship Officer( CRO ) throughout the processing of the loan.

        <p><em>Please note that the initial processing fee cheque submitted by you at the time of your application 
        will be banked immediately and is non-refundable.</em></p>

        <p>Kindly acknowledge this mail and confirm the date of funds required for the said loan.</p>
        <p>CRO Name:{employee_data['name']}</p>
        <p>Contact Number: {employee_data['phone_no']}</p>
        <p>Email ID : {employee_data['email']}</p>
        <p>Office Address:{loan_data['bank_address']}</p>


        <p>We request you to kindly use the reference number shared in this mail for all future correspondence with us.</p>

        <p>We look forward to your continued patronage.</p>

        <p>--</p>

        <p><strong>Thanks & Regards</strong></p>
        <p>{employee_data['name']}</p>
        <p>Customer Relationship Officer</p>
        <p>{loan_data['bank_address']}</p>
    </body>
    </html>
    """



# ✅ Initialize Gemini 1.5 Pro LLM
llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", google_api_key=GEMINI_API_KEY)

# ✅ Define tools
from langchain.tools import Tool

tools = [
    Tool(name="Fetch Customer Details", func=fetch_customer_details, description="Fetches customer details from MongoDB."),
    Tool(name="Generate Loan Report", func=generate_loan_report, description="Creates a loan approval report in HTML format."),
    Tool(name="Generate PDF", func=generate_pdf, description="Converts an HTML report into a PDF file."),
    Tool(name="Send Email", func=send_email, description="Sends an email with the attached loan approval PDF."),
    Tool(name="Loan Recommendation", func=generate_loan_recommendation, description="Generates AI-powered loan recommendations.")
]


@router.get("/onboard/")
def onboard_customer(current_user: str = Depends(get_current_user)):
    try:
        file_path = get_latest_file()
        pan_card = get_pan_number(file_path)
        
        if not pan_card:
            raise HTTPException(status_code=400, detail="No valid PAN number found in the document.")
        
        # Fetch customer details
        loan_data, applicant_data = fetch_customer_details(pan_card)
        employee_data = staff_collection.find_one({"username":current_user})
        if not employee_data:
            raise HTTPException(status_code=404,detail="Employee data not found for current user")
        # Generate Loan Recommendation Email
        email_subject = "Loan Approval-Welcome mail"
        email_body = generate_loan_recommendation(loan_data, applicant_data,employee_data)

        return {
            "email_subject": email_subject,
            "email_body": email_body,
            "recipient_email": loan_data.get("Email")
        }

    except Exception as e:
        logging.error(f"Error during onboarding: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# 📌 **Send Edited Email (Now Sends PDF as Attachment)**
@router.post("/sendemail/")
def send_email_api(data: dict, current_user: str = Depends(get_current_user)):
    try:
        logging.info(f"📩 Received email request: {data}")
        
        # Ensure all required keys exist
        if not all(k in data for k in ["recipient_email", "subject", "body"]):
            raise ValueError("❌ Missing required email fields")

        # Ensure no None values
        if any(v is None for v in data.values()):
            raise ValueError("❌ Some email fields are None")
        
        # Generate the PDF attachment using the same steps as your onboarding flow:
        # 1. Get the latest file (PAN card image or pdf)
        file_path = get_latest_file()
        # 2. Extract PAN number
        pan_card = get_pan_number(file_path)
        if not pan_card:
            raise HTTPException(status_code=400, detail="No valid PAN number found in the document.")
        
        # 3. Fetch customer details from MongoDB
        loan_data, applicant_data = fetch_customer_details(pan_card)
        employee_data = staff_collection.find_one({"username":current_user})
        if not employee_data:
            raise HTTPException(status_code=404,detail="Employee data not found for current user")
        
        # 4. Generate Loan Report in HTML format
        loan_report_html = generate_loan_report(loan_data, applicant_data,employee_data)
        
        # 5. Convert the HTML report to a PDF file
        pdf_path = generate_pdf(loan_report_html, f"Loan_Report_{pan_card}.pdf")
        
        # Send email with the PDF attached
        send_email(data["recipient_email"], data["subject"], data["body"], pdf_path)
        return {"message": "✅ Email sent successfully!"}

    except Exception as e:
        logging.error(f"❌ Error sending email: {e}")
        raise HTTPException(status_code=500, detail=str(e))