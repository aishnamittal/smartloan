import os
import json
import sys
from pymongo import MongoClient
from dotenv import load_dotenv
from langgraph.graph import StateGraph
from pydantic import BaseModel
from typing import Optional, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langsmith import trace
from langchain.globals import set_debug
from langchain.schema import SystemMessage
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from langchain.tools import StructuredTool


# ------------------------- SETUP ------------------------- #
# Set encoding to UTF-8 to avoid Unicode errors
sys.stdout.reconfigure(encoding='utf-8')

# Enable LangSmith Debugging
set_debug(True)

# Load environment variables
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))  # Default to 587 if not set
SMTP_USER = os.getenv("SMTP_USER")  # Your Gmail address
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")  # Your Gmail App Password

# Validate API keys
if not GEMINI_API_KEY:
    raise ValueError("❌ Missing GEMINI_API_KEY! Please set it in the .env file.")
if not MONGO_URI:
    raise ValueError("❌ Missing MONGO_URI! Please set it in the .env file.")

# Initialize MongoDB connection (moved outside function)
client = MongoClient(MONGO_URI)
db = client["Dummy_data"]  # Database name
loan_collection = db["loan-info"]
credit_collection = db["credit_score_info"]

# Initialize AI Model (moved outside function)
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro-latest",
    google_api_key=GEMINI_API_KEY,
    temperature=0.7
)

memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# ------------------------- STATE MODEL ------------------------- #
class RiskAssessmentState(BaseModel):
    pan_card: str
    credit_score: Optional[int] = None
    salary_slip_verified: Optional[bool] = True
    delinquency_history: Optional[int] = None
    requested_loan_amount: Optional[float] = None
    requested_loan_type: Optional[str] = None
    max_possible_loan: Optional[float] = None
    loan_eligibility: Optional[str] = "Pending"
    fraud_check_passed: Optional[bool] = None
    final_report: Optional[str] = None
    monthly_income: Optional[float] = None
    other_loan_payments: Optional[float] = 0.0  # Default value if not provided
    Net_Pay: Optional[float]=None

# ------------------------- DATABASE FETCH FUNCTION ------------------------- #
def fetch_customer_data(pan_card: str):
    """Fetch customer data from MongoDB based on PAN card."""
    print(f"🔍 Fetching data for PAN: {pan_card}...")
    credit_info = credit_collection.find_one({"Pan-card": pan_card})
    loan_info = loan_collection.find_one({"Pan-card": pan_card})

    if not credit_info or not loan_info:
        raise ValueError("❌ Customer data not found!")

    net_pay = credit_info.get("Net_Pay")

    return {
        "pan_card": pan_card,
        "credit_score": credit_info.get("Credit_Score"),
        "salary_slip_verified": bool(net_pay),
        "delinquency_history": credit_info.get("num_times_delinquent"),
        "requested_loan_amount": loan_info.get("loan_amount"),
        "requested_loan_type": loan_info.get("loan_type"),
        "monthly_income": credit_info.get("Net_Monthly_Income"),
        "other_loan_payments": credit_info.get("other_loans", 0.0),
        "Net_Pay": credit_info.get("Net_Pay")
    }

# ------------------------- TOOLS ------------------------- #
def compute_max_loan(monthly_income: float, credit_score: int, other_loans: float) -> float:
    """Calculate max loan based on income and existing loans."""
    max_loan = (monthly_income * 10) - other_loans  
    return max_loan if max_loan > 0 else 0  

loan_tool = StructuredTool.from_function(
    name="Loan Calculator",
    func=compute_max_loan,
    description="Calculates max possible loan based on income and debt."
)


# ------------------------- AGENTS WITH LANGSMITH TRACING ------------------------- #
# ------------------------- AI AGENTS ------------------------- #
# ------------------------- AGENTS (TOOL-BASED + LLM ONLY WHERE NEEDED) ------------------------- #

def credit_history_agent(state: RiskAssessmentState) -> RiskAssessmentState:
    """Agent assesses creditworthiness using logic or LLM if unclear."""
    
    credit_score = state.credit_score
    delinquency = state.delinquency_history.lower() if isinstance(state.delinquency_history, str) else None

    if credit_score is not None and delinquency in ("yes", "no"):
        if credit_score >= 700 and delinquency == "no":
            state.loan_eligibility = "Approved"
            state.final_report = "Approved based on good credit score and no delinquency."
            return state
        elif credit_score < 600 and delinquency == "yes":
            state.loan_eligibility = "Rejected"
            state.final_report = "Rejected due to poor credit score and delinquency."
            return state
        else:
            state.final_report = "Credit score or delinquency unclear for direct rule-based decision."

    # Only call LLM if rule-based logic couldn't decide
    if state.loan_eligibility is None:
        prompt = f"""
        Evaluate customer credit risk:
        - Credit Score: {credit_score}
        - Delinquency History: {state.delinquency_history}

        Should the loan be approved? Reply with 'Approved' or 'Rejected' and reasoning.
        """
        response = llm.predict(prompt)
        state.loan_eligibility = "Rejected" if "Rejected" in response else "Approved"
        state.final_report = response
    
    return state


def max_loan_agent(state: RiskAssessmentState) -> RiskAssessmentState:
    """Agent computes maximum possible loan amount using a tool (always)."""
    
    monthly_income = state.monthly_income or 0.0
    other_loans = state.other_loan_payments or 0.0

    # Always use tool here
    state.max_possible_loan = loan_tool.run({
        "monthly_income": monthly_income, 
        "credit_score": state.credit_score, 
        "other_loans": other_loans
    })
    return state


def loan_approval_agent(state: RiskAssessmentState) -> RiskAssessmentState:
    """Agent makes final approval decision using LLM (requires reasoning)."""

    # This agent requires judgment + natural language explanation
    prompt = f"""
    Based on the following:
    - Requested Loan Amount: {state.requested_loan_amount}
    - Max Possible Loan: {state.max_possible_loan}
    - Fraud Check Passed: {state.fraud_check_passed}

    Approve or reject the loan with reasoning.
    Reply with either 'Approved' or 'Rejected' followed by an explanation. start the sentence with 'Approved' or 'Rejected'
    All amount values are in Rs. that is ₹ symbol

    """
    response = llm.predict(prompt)

    if "Rejected" in response:
        state.loan_eligibility = "Rejected"
    else:
        state.loan_eligibility = "Approved"

    state.final_report = response
    return state


# ------------------------- LANGGRAPH IMPLEMENTATION ------------------------- #
class RiskAssessmentGraph:
    def __init__(self):
        """Defines the AI agent workflow using LangGraph."""
        self.graph = StateGraph(RiskAssessmentState)

        # Adding nodes (agents)
        self.graph.add_node("Credit History Check", credit_history_agent)
        self.graph.add_node("Calculate Max Loan", max_loan_agent)
        self.graph.add_node("Final Loan Approval", loan_approval_agent)

        # Defining workflow connections
        self.graph.add_edge("Credit History Check", "Calculate Max Loan")
        self.graph.add_edge("Calculate Max Loan", "Final Loan Approval")

        # Set entry and exit points
        self.graph.set_entry_point("Credit History Check")
        self.graph.set_finish_point("Final Loan Approval")

        self.compiled_graph = self.graph.compile()

    def run(self, input_state: Dict[str, Any]):
        initial_state = RiskAssessmentState(**input_state)
        final_state = self.compiled_graph.invoke(initial_state)
        return final_state


# ------------------------- FINAL REPORT PRINT FUNCTION ------------------------- #
def calculate_loan_score(state):
    """Calculates a loan eligibility score out of 10 based on creditworthiness."""
    score = 0

    # Credit Score Contribution
    if state.get("credit_score") >= 750:
        score += 4  # Very good credit
    elif state.get("credit_score") >= 650:
        score += 3  # Good credit
    elif state.get("credit_score") >= 600:
        score += 2  # Average credit
    else:
        score += 1  # Poor credit

    # Delinquency History Impact
    if state.get("delinquency_history", 0) == 0:
        score +=3  # No missed payments
    elif state.get("delinquency_history", 0) <= 2:
        score += 1  # Few missed payments
    else:
        score -= 1  # High risk due to multiple missed payments

    # Loan Affordability (Income vs. Debt)
    max_loan = state.get("max_possible_loan", 0)
    requested_loan = state.get("requested_loan_amount", 0)
    if requested_loan <= max_loan:
        score += 2  # Affordable loan request
    else:
        score -= 1  # Asked for more than eligible

    return max(1, min(10, score))  # Ensure score is within 1-10

def print_final_report(state):
    """Prints the loan decision step-by-step in a human-friendly format."""
    print("\n📢 FINAL LOAN ASSESSMENT REPORT")
    print("=" * 50)

    # Step 1: Customer Details
    print(f"👤 Customer PAN: {state.get('pan_card', 'N/A')}")
    print(f"💳 Credit Score: {state.get('credit_score', 'N/A')} ({'Good' if state.get('credit_score', 0) >= 600 else 'Low'})")
    print(f"📄 Salary Slip Verified: {'✅ Yes' if state.get('salary_slip_verified', False) else '❌ No'}")
    print(f"🔄 Delinquency History: {state.get('delinquency_history', 0)} missed payments")

    print("\n📌 Loan Request Details")
    print(f"🏦 Requested Loan Amount: ₹{state.get('requested_loan_amount', 0):,.2f}")
    print(f"📚 Loan Type: {state.get('requested_loan_type', 'N/A')}")
    print(f"💰 Monthly Income: ₹{state.get('monthly_income', 0):,.2f}")
    print(f"💸 Other Loan Payments: ₹{state.get('other_loan_payments', 0):,.2f}")

    # Step 2: Risk Assessment Breakdown
    print("\n🔍 Risk Assessment Summary")

    print(f"... 📊 Maximum Eligible Loan: ₹{state.get('max_possible_loan', 0):,.2f}")

    # Loan Eligibility Score
    loan_score = calculate_loan_score(state)
    print(f"\n🏆 **Loan Eligibility Score: {loan_score}/10**")

    # Step 3: Final Decision
    print("\n⚖ Loan Approval Decision")
    if state.get("loan_eligibility") == "Rejected":
        print(f"❌ Loan Rejected: {state.get('final_report', 'Reason not specified')}")
    else:
        print(f"✅ Loan Approved! {state.get('final_report', 'Approval details not provided')}")

    print("=" * 50)

def send_rejection_email(state):
    """Sends an email notification to the customer if the loan is rejected."""
    # Fetch customer's email from MongoDB
    customer_info = loan_collection.find_one({"Pan-card": state.get("pan_card")})
    if not customer_info or "Email" not in customer_info:
        print("⚠ No email found for the customer. Skipping email notification.")
        return None

    customer_email = customer_info["Email"]
    print(f"📧 Sending email to: {customer_email}")
    
    # Define Email Subject & Body
    subject = "Loan Application Status - Rejected"
    body = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6;">
    <p>Dear Customer,</p>

    <p>We regret to inform you that your recent loan application has been
    <strong style="color: red;">rejected</strong>.</p>

    <h3 style="color: #2C3E50;">Loan Application Summary</h3>
    <table style="border-collapse: collapse; width: 100%;">
        <tr><td><strong>Customer PAN:</strong></td><td>{state.get('pan_card', 'N/A')}</td></tr>
        <tr><td><strong>Credit Score:</strong></td><td>{state.get('credit_score', 'N/A')} ({'Good' if state.get('credit_score', 0) >= 600 else 'Low'})</td></tr>
        <tr><td><strong>Salary Slip Verified:</strong></td><td>{'Yes' if state.get('salary_slip_verified', False) else 'No'}</td></tr>
        <tr><td><strong>Delinquency History:</strong></td><td>{state.get('delinquency_history', 0)} missed payments</td></tr>
    </table>

    <h3 style="color: #2C3E50;">Loan Request Details</h3>
    <table style="border-collapse: collapse; width: 100%;">
        <tr><td><strong>Requested Loan Amount:</strong></td><td>₹{state.get('requested_loan_amount', 0):,.2f}</td></tr>
        <tr><td><strong>Loan Type:</strong></td><td>{state.get('requested_loan_type', 'N/A')}</td></tr>
        <tr><td><strong>Monthly Income:</strong></td><td>₹{state.get('monthly_income', 0):,.2f}</td></tr>
        <tr><td><strong>Other Loan Payments:</strong></td><td>₹{state.get('other_loan_payments', 0):,.2f}</td></tr>
    </table>

    <h3 style="color: #2C3E50;">Risk Assessment Summary</h3>
    <table style="border-collapse: collapse; width: 100%;">
        <tr><td><strong>Maximum Eligible Loan:</strong></td><td>₹{state.get('max_possible_loan', 0):,.2f}</td></tr>
    </table>

    <h3 style="color: #E74C3C;">Loan Eligibility Score: {calculate_loan_score(state)}/10</h3>

    <h3 style="color: #E74C3C;">Loan Approval Decision</h3>
    <p style="color: red;"><strong>Loan Rejected:</strong> {state.get('final_report', 'Reason not specified')}</p>

    <h3 style="color: #D35400;">Loan Rejection Explanation</h3>
    <p>After reviewing your application, we found that your requested loan amount was **significantly higher** than your financial eligibility.</p>

    <ul>
        <li>Your requested loan amount (₹{state.get('requested_loan_amount', 0):,.2f}) exceeds the maximum eligible amount (₹{state.get('max_possible_loan', 0):,.2f}).</li>
        <li>Your credit score ({state.get('credit_score', 'N/A')}) is lower than the required threshold for this loan type.</li>
        <li>You have a history of missed payments, which negatively affects your creditworthiness.</li>
    </ul>

    <p>To improve your chances of loan approval in the future, consider:</p>
    <ul>
        <li>Applying for a lower loan amount within your eligibility range.</li>
        <li>Improving your credit score by ensuring timely payments.</li>
        <li>Reducing your existing debt and increasing your monthly income.</li>
    </ul>

    <p>If you have any questions or need assistance in improving your creditworthiness, please contact our support team.</p>

    <p>Best regards,<br>
    <strong>Loan Risk Assessment Team</strong></p>
</body>
</html>
"""
    email_data = {
        "pan_card": state.get("pan_card"),
        "email": customer_email,
        "subject": subject,
        "email_content": body,
    }

    print("Email Content Generated:", email_data)
    return email_data  # Return email instead of storing it

def send_acceptance_email(state):

    """Sends an email notification to the customer if the loan is accepted."""
    # Fetch customer's email from MongoDB
    customer_info = loan_collection.find_one({"Pan-card": state.get("pan_card")})
    if not customer_info or "Email" not in customer_info:
        print("⚠ No email found for the customer. Skipping email notification.")
        return None

    customer_email = customer_info["Email"]
    print(f"📧 Sending email to: {customer_email}")
    
    # Define Email Subject & Body
    subject = "Loan Application Status - Approved"
    body = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6;">
    <p>Dear Customer,</p>

    <p>We are pleased to inform you that your recent loan application has been
    <strong style="color: green;">approved</strong></p>

    <h3 style="color: #2C3E50;">Loan Application Summary</h3>
    <table style="border-collapse: collapse; width: 100%;">
        <tr><td><strong>Customer PAN:</strong></td><td>{state.get('pan_card', 'N/A')}</td></tr>
        <tr><td><strong>Credit Score:</strong></td><td>{state.get('credit_score', 'N/A')} ({'Good' if state.get('credit_score', 0) >= 600 else 'Average'})</td></tr>
        <tr><td><strong>Salary Slip Verified:</strong></td><td>{'Yes' if state.get('salary_slip_verified', False) else 'No'}</td></tr>
        <tr><td><strong>Delinquency History:</strong></td><td>{state.get('delinquency_history', 0)} missed payments</td></tr>
    </table>

    <h3 style="color: #2C3E50;">Loan Request Details</h3>
    <table style="border-collapse: collapse; width: 100%;">
        <tr><td><strong>Requested Loan Amount:</strong></td><td>₹{state.get('requested_loan_amount', 0):,.2f}</td></tr>
        <tr><td><strong>Loan Type:</strong></td><td>{state.get('requested_loan_type', 'N/A')}</td></tr>
        <tr><td><strong>Monthly Income:</strong></td><td>₹{state.get('monthly_income', 0):,.2f}</td></tr>
        <tr><td><strong>Other Loan Payments:</strong></td><td>₹{state.get('other_loan_payments', 0):,.2f}</td></tr>
    </table>

    <h3 style="color: #2C3E50;">Risk Assessment Summary</h3>
    <table style="border-collapse: collapse; width: 100%;">
        <tr><td><strong>Maximum Eligible Loan:</strong></td><td>₹{state.get('max_possible_loan', 0):,.2f}</td></tr>
    </table>

    <h3 style="color: #27AE60;">Loan Eligibility Score: {calculate_loan_score(state)}/10</h3>

    <h3 style="color: #27AE60;">Loan Approval Decision</h3>
    <p style="color: green;"><strong>Loan Approved:</strong> {state.get('final_report', 'You met all eligibility criteria.')}</p>

    <h3 style="color: #2980B9;">Next Steps</h3>
    <ul>
        <li>A detailed loan document will be shared with you shortly for your review and signature.</li>
        <li>The sanctioned loan amount of ₹{state.get('requested_loan_amount', 0):,.2f} will be disbursed upon completion of formalities.</li>
        <li>Our relationship manager will get in touch with you within 24 hours for further assistance.</li>
    </ul>

    <p>If you have any questions or need assistance, feel free to reach out to our support team.</p>

    <p>Congratulations once again, and thank you for choosing our services!</p>

    <p>Best regards,<br>
    <strong>Loan Risk Assessment Team</strong></p>
</body>
</html>
"""
    email_data = {
        "pan_card": state.get("pan_card"),
        "email": customer_email,
        "subject": subject,
        "email_content": body,
    }

    print("✅ Email Content Generated:", email_data)
    return email_data  # Return email instead of storing it

