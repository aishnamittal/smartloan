import React, { useState, useEffect } from "react";
import axios from "axios";
import "./onboarding.css";
import Disbursement from "./Disbursement.js";
// Disbursement component will be rendered via routing, no need to import directly.
// import { useNavigate } from "react-router-dom";

const Onboarding = () => {
    const [emailContent, setEmailContent] = useState("");
    const [editedEmailContent, setEditedEmailContent] = useState("");
    const [subject, setSubject] = useState("");
    const [recipientEmail, setRecipientEmail] = useState(""); // State for recipient email
    const [isEditing, setIsEditing] = useState(false);
    const [emailStatus, setEmailStatus] = useState("");
    // const navigate = useNavigate(); // Hook for navigation

    useEffect(() => {
        const token = localStorage.getItem("access_token"); // ✅ Token must be stored at login
    
        axios.get("http://127.0.0.1:8000/onboard/", {
            headers: {
                Authorization: `Bearer ${token}` // ✅ Add token to Authorization header
            }
        })
        .then(response => {
            console.log("✅ Full API Response:", response.data);
    
            if (!response.data) {
                console.warn("⚠ Response is empty");
                return;
            }
    
            if ("email_body" in response.data) {
                console.log("📩 Email content exists:", response.data.email_body);
                const plainText = response.data.email_body.replace(/<[^>]+>/g, ""); 
                setEmailContent(plainText);
                setEditedEmailContent(plainText);
            } else {
                console.warn("⚠ No email_body field found in API response.");
                setEmailContent("⚠ No email preview available.");
                setEditedEmailContent("⚠ No email preview available.");
            }
    
            if ("email_subject" in response.data) {
                setSubject(response.data.email_subject);
            }
            if ("recipient_email" in response.data) {
                setRecipientEmail(response.data.recipient_email);
            }
    
        })
        .catch(error => {
            console.error("❌ Error fetching email:", error);
            setEmailContent("❌ Failed to load email.");
            setEditedEmailContent("❌ Failed to load email.");
        });
    }, []);
    
    
    const handleEdit = () => {
        setIsEditing(!isEditing);
    };

    const handleSendEmail = () => {
        const emailToSend = isEditing ? editedEmailContent : emailContent;
        const token = localStorage.getItem("access_token");
    
        axios.post("http://127.0.0.1:8000/sendemail/", {
            recipient_email: recipientEmail,
            subject: subject,
            body: emailToSend
        }, {
            headers: {
                Authorization: `Bearer ${token}` // ✅ This is required for auth
            }
        })
        .then(response => {
            console.log("✅ Email sent:", response.data);
            setEmailStatus("✅ Email sent successfully!");
        })
        .catch(error => {
            console.error("❌ Failed to send email:", error);
            setEmailStatus("❌ Failed to send email.");
        });
    };
    

    return (
        <div className="onboarding-container">
            <h2>Onboarding Email</h2>
            <input 
                type="text" 
                value={subject} 
                onChange={(e) => setSubject(e.target.value)} 
                readOnly={!isEditing} 
            />
            <textarea 
                value={editedEmailContent} 
                onChange={(e) => setEditedEmailContent(e.target.value)} 
                readOnly={!isEditing} 
            />
            <button className = "edit-btn" onClick={handleEdit}>{isEditing ? "Save & Preview" : "Edit"}</button>
            <button className = "send-email-btn" onClick={handleSendEmail}>Send Email</button>
            {emailStatus && <p>{emailStatus}</p>}
        </div>
    );
};

export default Onboarding;