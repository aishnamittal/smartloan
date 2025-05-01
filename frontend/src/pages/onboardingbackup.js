// import React, { useState, useEffect } from "react";
// import axios from "axios";
// import "./onboarding.css";
// import Disbursement from "./Disbursement.js";
// // Disbursement component will be rendered via routing, no need to import directly.
// import { useNavigate } from "react-router-dom";

// const Onboarding = () => {
//     const [emailContent, setEmailContent] = useState("");
//     const [editedEmailContent, setEditedEmailContent] = useState("");
//     const [subject, setSubject] = useState("");
//     const [recipientEmail, setRecipientEmail] = useState(""); // State for recipient email
//     const [isEditing, setIsEditing] = useState(false);
//     const [emailStatus, setEmailStatus] = useState("");
//     const navigate = useNavigate(); // Hook for navigation

//     useEffect(() => {
//         axios.get("http://127.0.0.1:8000/onboard")
//             .then(response => {
//                 console.log("✅ Full API Response:", response.data);
    
//                 if (!response.data) {
//                     console.warn("⚠ Response is empty");
//                     return;
//                 }
    
//                 // Fix: Use correct field names from API response
//                 if ("email_body" in response.data) {
//                     console.log("📩 Email content exists:", response.data.email_body);
//                     const plainText = response.data.email_body.replace(/<[^>]+>/g, ""); 
//                     setEmailContent(plainText);
//                     setEditedEmailContent(plainText);
//                 } else {
//                     console.warn("⚠ No email_body field found in API response.");
//                     setEmailContent("⚠ No email preview available.");
//                     setEditedEmailContent("⚠ No email preview available.");
//                 }
    
//                 if ("email_subject" in response.data) {
//                     setSubject(response.data.email_subject);
//                 }
//                 if ("recipient_email" in response.data) {
//                     setRecipientEmail(response.data.recipient_email);
//                 }
    
//             })
//             .catch(error => {
//                 console.error("❌ Error fetching email:", error);
//                 setEmailContent("❌ Failed to load email.");
//                 setEditedEmailContent("❌ Failed to load email.");
//             });
//     }, []);
    
    
//     const handleEdit = () => {
//         setIsEditing(!isEditing);
//     };

//     const handleSendEmail = () => {
//         const emailToSend = isEditing ? editedEmailContent : emailContent;

//         axios.post("http://127.0.0.1:8000/sendemail/", {
//             recipient_email:recipientEmail,
//             subject: subject,
//             body: emailToSend
//         })
//             .then(response => {
//                 console.log("✅ Email sent:", response.data);
//                 setEmailStatus("✅ Email sent successfully!");
//             })
//             .catch(error => {
//                 console.error("❌ Failed to send email:", error);
//                 setEmailStatus("❌ Failed to send email.");
//             });
//     };

//     return (
//         <div className="onboarding-container">
//             <h2>Onboarding Email</h2>
//             <input 
//                 type="text" 
//                 value={subject} 
//                 onChange={(e) => setSubject(e.target.value)} 
//                 readOnly={!isEditing} 
//             />
//             <textarea 
//                 value={editedEmailContent} 
//                 onChange={(e) => setEditedEmailContent(e.target.value)} 
//                 readOnly={!isEditing} 
//             />
//             <button onClick={handleEdit}>{isEditing ? "Save & Preview" : "Edit"}</button>
//             <button onClick={handleSendEmail}>Send Email</button>
//             {/* <button className="next-button" onClick={Disbursement}>Next Step</button> */}
//             {/* Redirect to Disbursement component which auto-starts disbursement */}
//             <button className="next-button" onClick={() => navigate("/disbursement")}>Next Step</button>
//             {emailStatus && <p>{emailStatus}</p>}
//         </div>
//     );
// };

// export default Onboarding;

import React, { useState, useEffect } from "react";
import axios from "axios";
import "./Disbursement.css";

const Disbursement = function DisbursementComponent() {
  const [loanDetails, setLoanDetails] = useState(null);
  const [error, setError] = useState(null);

  const fetchDisbursementDetails = async () => {
    try {
      const response = await axios.post(
        "http://127.0.0.1:8000/disburse-loan/",
        {},
        { headers: { "Content-Type": "application/json" } }
      );
      setLoanDetails(response.data);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to fetch loan details.");
      setLoanDetails(null);
    }
  };
useEffect(() => {
  fetchDisbursementDetails();
}, []);
  return (
    <div className="container">
      <div className="disbursement-container">
        <h2>Loan Disbursement</h2>
      </div>
      <div>
        {loanDetails && (
          <div className="loan-details">
            <h3>Loan Disbursement Details</h3>
            <p><strong>Applicant Name:</strong> {loanDetails.applicant_name}</p>
            <p><strong>Application Number:</strong> {loanDetails.application_number}</p>
            <p><strong>Loan Amount:</strong> {loanDetails.loan_amount}</p>
            <p><strong>Disbursed Amount:</strong> {loanDetails.disbursed_amount}</p>
            <p><strong>Remaining Amount:</strong> {loanDetails.remaining_amount}</p>
            <p><strong>Status:</strong> {loanDetails.disbursement_status}</p>
          </div>
        )}
        {error && <p className="error-message">❌ {error}</p>}
      </div>
    </div>
  );
};

export default Disbursement;
