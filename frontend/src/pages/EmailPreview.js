import React, { useState, useEffect } from "react";
import axios from "axios";

const EmailPreview = ({ emailData }) => {  
  const [emailContent, setEmailContent] = useState("");  // Original email content
  const [editedEmailContent, setEditedEmailContent] = useState("");  // Stores edited content
  const [subject, setSubject] = useState("");
  const [emailStatus, setEmailStatus] = useState("");
  const [isEditing, setIsEditing] = useState(false);
  const [isEdited, setIsEdited] = useState(false);  // Track if edited

  useEffect(() => {
    if (emailData?.email_content) {
      const plainText = emailData.email_content.replace(/<[^>]+>/g, "");
      setEmailContent(plainText);
      setEditedEmailContent(plainText);
      setSubject(emailData.subject);
    } else {
      setEmailContent("⚠ No email preview available.");
      setEditedEmailContent("⚠ No email preview available.");
    }
  }, [emailData]);
  

  const handleSendEmail = () => {
    const emailToSend = isEdited ? editedEmailContent : emailContent; // Use edited if available

    axios.post("http://127.0.0.1:8000/send-email", { 
        subject: subject,
        email_content: emailToSend
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

  const handleEdit = () => {
    setIsEditing(!isEditing);
    setIsEdited(true);  // Mark as edited
  };

  return (
    <div className="email-container" style={{ padding: "20px", maxWidth: "600px", margin: "auto" }}>
      <h2>Email Preview</h2>
      <h3>{subject}</h3>

      {!isEditing ? (
        <div
          style={{
            width: "auto",
            height: "200px",
            overflowY: "auto",
            padding: "10px",
            border: "1px solid #ccc",
            borderRadius: "5px",
            background: "#fff",
            color: "#000",
            whiteSpace: "pre-wrap"
          }}
        >
          {editedEmailContent.includes("<") ? (
            <div dangerouslySetInnerHTML={{ __html: editedEmailContent }} />
          ) : (
            <pre>{editedEmailContent}</pre>
          )}
        </div>
      ) : (
        <textarea
          value={editedEmailContent}
          onChange={(e) => setEditedEmailContent(e.target.value)}
          rows={10}
          cols={50}
          style={{
            width: "100%",
            height: "200px",
            padding: "10px",
            border: "1px solid #ccc",
            borderRadius: "5px",
            background: "#fff",
            color: "#000"
          }}
        />
      )}

      <button onClick={handleEdit} style={{ marginTop: "10px", marginRight: "10px", padding: "10px 20px", background: isEditing ? "#28a745" : "#ffc107", color: "#fff", border: "none", borderRadius: "5px", cursor: "pointer" }}>
        {isEditing ? "Save & Preview" : "Edit Email"}
      </button>
      <button onClick={handleSendEmail} style={{ marginTop: "10px", padding: "10px 20px", background: "#007bff", color: "#fff", border: "none", borderRadius: "5px", cursor: "pointer" }}>
        Send Mail
      </button>
      {emailStatus && <p>{emailStatus}</p>}
    </div>
  );
};

export default EmailPreview;

