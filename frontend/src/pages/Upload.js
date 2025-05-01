
import React, { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";
import { FaPaperclip } from "react-icons/fa"; // Importing paperclip icon
import axios from "axios";
import { FaUser } from "react-icons/fa";
import "./Upload.css"; // Ensure you have styles for UI
import OnboardingTab from "./onboarding"; // Import the Onboarding component
import { useNavigate } from "react-router-dom";
import EmailPreview from "./EmailPreview";  // Adjust path if needed
import Disbursement from "./Disbursement.js"; // Import Disbursement component
import LoanRiskDropdown from './LoanRiskDropdown';
import KYCDetails from "./KYCDetails";
import CardViewer from './CardViewer'; // adjust path as needed


const Upload = () => {
  const [kycVerified, setKycVerified] = useState(null);
  const location = useLocation();
  const initialUser = location.state?.user || { name: "Default Name", lanNumber: "Default LAN" };
  const initialTab = location.state?.activeTab || "Upload";
  const [activeTab, setActiveTab] = useState(initialTab);
  const [files, setFiles] = useState({});
  const [uuid, setUuid] = useState(null);
  const navigate = useNavigate();
  const [loanDetails, setLoanDetails] = useState(null);
  const [loanScore, setLoanScore] = useState(null);
  const [uploadStatus, setUploadStatus] = useState({});
  const [kycStepIndex, setKycStepIndex] = useState(-1); // New state to track steps
  const [kycLoading, setKycLoading] = useState(false); // New state for loading status
  const [riskStepIndex, setriskStepIndex] = useState(-1);
  const [riskLoading, setriskLoading] = useState(false);
  const [emailData, setEmailData] = useState(null);
  const [riskStatus, setriskStatus] = useState(null);
  const [showEndButton, setShowEndButton] = useState(false);
  const backendUrl = "http://127.0.0.1:8000/upload/";
   // New state for the JotForm URL that will be updated with prepopulation data
  const [formUrl, setFormUrl] = useState("https://form.jotform.com/251141777133049");
  const kycVerifyUrl = "http://127.0.0.1:8000/KYC"; // Backend endpoint for KYC verification
  const kycSteps = [ // Steps displayed in sequence
    "📑 KYC process started",
    "📂 Getting Your Documents ready",
    "🔍 Fetching your details",
    "📝 Scanning your documents",
    "🔄 Cross-checking with the database",
    "📡 Contacting verification servers",
    "✅ Verifying your documents",
    "📊 Finalizing your verification",
  ];
  const riskSteps = [// Steps displayed in sequence
    "📑 Risk assessment process started",
    "📂 Getting Your Documents ready",
    "🔍 Fetching your details",
    "📝 Scanning your documents",
    "🔄 Cross-checking with the database",
    "✅ Verifying your documents",
    "📊 Finalizing your verification",
    "🔍 Risk Assessment Summary",
    "⚖ Loan Decision Based on AI"
  ];
  const [selectedDropdown, setSelectedDropdown] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    panNumber: '',
    aadharNumber: '',
    disbursementAmount: ''
  });

  const handleFileChange = (e, docType) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFiles((prevFiles) => ({ ...prevFiles, [docType]: selectedFile }));
    }
  };
 
  const handleUpload = async (docType) => {
    setActiveTab("Upload");
    if (!files[docType]) {
      return;
    }

    const formData = new FormData();
    formData.append("document_type", docType);
    formData.append("file", files[docType]);

    try {
      await axios.post(backendUrl, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      setUploadStatus((prevStatus) => ({
        ...prevStatus,
        [docType]: "success",
      }));

    } catch (error) {
      setUploadStatus((prevStatus) => ({
        ...prevStatus,
        [docType]: "error",
      }));
    }
  };
  const updateLoanCompletionStatus = async (status = "Completed") => {
    const uuid = localStorage.getItem("loanApplicationUUID");
    if (!uuid) {
      console.warn("⚠️ No UUID found in localStorage");
      return;
    }
  
    try {
      await axios.put(`http://127.0.0.1:8000/api/loan-complete-status/${uuid}`, null, {
        params: { completeStatus: status },
      });
      console.log(`✅ Loan completion status set to: ${status}`);
    } catch (error) {
      console.error("❌ Error updating loan completion status:", error);
    }
  };
  
  
  const handleRiskAssessment = async () => {
    setActiveTab("Risk Assessment Agent");
    setriskStepIndex(0);
    setriskLoading(true);
 
    
    try {
      console.log("Risk Assessment Started, But API call pending");

    } catch (error) {
      console.error("Risk assessment request failed:", error);
    }
  };
  const fetchRiskAssessment = async () => {
    try {
      const response = await axios.get("http://127.0.0.1:8000/risk-assessment/");
      console.log("📊 Risk Data:", response.data);
  
      // Set Loan Score and Details
      setLoanScore(response.data.loan_score);
      setLoanDetails(response.data);
      setEmailData(response.data);
  
      // ✅ Set Risk Status based on eligibility
      if (response.data.loan_status?.loan_eligibility === "Approved") {
        setriskStatus("🎉 Customer is Eligible for Loan");
      } else {
        setriskStatus("❌ Customer is not Eligible for Loan");
      }
  
    } catch (err) {
      console.error("❌ Risk fetch failed:", err);
      setriskStatus("❌ Risk assessment Failed");
    }
  };
  const handleonboarding= async() => {
    setActiveTab("Onboarding Agent");
  };
  const generateNumericUUID = () => {
    return Math.floor(10000 + Math.random() * 90000).toString(); // Generate 5-digit number
};

  const handleVerifyClick = async () => {
    setActiveTab("KYC Agent"); 
    setKycStepIndex(0);
    setKycLoading(true);  

    try {
        // Generate UUID
        const generatedUuid = generateNumericUUID();
        console.log("Generated UUID:", generatedUuid);
        setUuid(generatedUuid);

        // ✅ Save to localStorage or sessionStorage
        localStorage.setItem("loanApplicationUUID", generatedUuid); // or sessionStorage.setItem()

        // Send to backend
        await axios.post("http://127.0.0.1:8000/api/loan-state", {
            loanApplicationNumber: generatedUuid,
            stage: "Upload"
        });
    } catch (error) {
        console.error("Error saving loan application:", error);
    }
};
const handleEndProcess = async () => {
  try {
    const storedUuid = localStorage.getItem("loanApplicationUUID");
    console.log("Finalizing process for UUID:", storedUuid);

    // Finalize process (e.g. cleanup)
    await axios.get("http://127.0.0.1:8000/finalize-process/", {
      params: { uuid: storedUuid },
    });

    // 🔥 New: Update completion status
    await updateLoanCompletionStatus("Completed");

    // Clean up local state
    localStorage.removeItem("loanApplicationUUID");
    navigate("/dashboard");
  } catch (error) {
    console.error("Error during finalization:", error);
  }
};

const handlerejection = async () => {
  try {
    const storedUuid = localStorage.getItem("loanApplicationUUID"); // Optional: Just for logging
    console.log("Finalizing process for UUID:", storedUuid);

    // ✅ Remove UUID
    localStorage.removeItem("loanApplicationUUID");
    console.log("UUID removed from localStorage");

    // Optional: Reset in-memory state if using useState
    // setUuid(null);

    navigate("/dashboard");
  } catch (error) {
    console.error("Error during finalization:", error);
  }
};

const storedUuid = localStorage.getItem("loanApplicationUUID");
const updateLoanStage = async (newStage, status = null) => {
  if (!uuid) return;

  try {
    await axios.put(`http://127.0.0.1:8000/api/loan-state/${uuid}`, null, {
      params: {
        new_stage: newStage,
        ...(status && { status }) // include status only if provided
      }
    });
    console.log(`Stage updated to: ${newStage} ${status ? `and status to: ${status}` : ''}`);
    setActiveTab(newStage);
  } catch (error) {
    console.error("Error updating loan stage/status:", error);
  }
};


const handleNextStep = () => {
  const stages = ["Upload", "KYC Agent", "Risk Assessment Agent", "Onboarding Agent","Review Details", "Disbursement"];
  const nextIndex = stages.indexOf(activeTab) + 1;

  if (nextIndex < stages.length) {
    const nextStage = stages[nextIndex];
    updateLoanStage(nextStage);
  }
};

const handlePreviousStep = () => {
  const stages = ["Upload", "KYC Agent", "Risk Assessment Agent", "Onboarding Agent", "Disbursement"];
  const prevIndex = stages.indexOf(activeTab) - 1;

  if (prevIndex >= 0) {
    const prevStage = stages[prevIndex];
    updateLoanStage(prevStage);
  }
};

  useEffect(() => { // Handles KYC step transitions
    if (activeTab === "KYC Agent" && kycLoading) {
      fetch(kycVerifyUrl)  // Update with your actual API URL
      .then(response => response.json())
      .then(data => setKycVerified(data.kyc_verified))
      .catch(error => console.error("Error fetching KYC status:", error));
      let stepIndex = 0;
      const interval = setInterval(() => {
        if (stepIndex < kycSteps.length) {
          setKycStepIndex(stepIndex);
          stepIndex++;
        } else {
          clearInterval(interval);
          setKycLoading(false);
          fetchKycVerified(); // Fetch backend verification status after steps finish
        }
      }, 2000);
      return () => clearInterval(interval);
    }
  }, [activeTab, kycLoading]);
  
  useEffect(() => { // Handles Risk Assessment step transitions
    if (activeTab === "Risk Assessment Agent" && riskLoading) {
      let stepIndex = 0;
      const interval = setInterval(() => {
        if (stepIndex < riskSteps.length) {
          setriskStepIndex(stepIndex);
          stepIndex++;
        } else {
          clearInterval(interval);
          setriskLoading(false);
          fetchRiskAssessment(); // Fetch backend verification status after steps finish
        }
      }, 2000);
      return () => clearInterval(interval);
    }
  }, [activeTab, riskLoading]);

  // Function to build prefilled JotForm URL with dummy data and redirect back to Onboarding

  
  
  
  useEffect(() => {
    const fetchAutofillData = async () =>{
    if (activeTab === "Review Details" && storedUuid) {
      try {
    fetch("http://localhost:8000/autofill/")
    .then(response => response.json())
        .then(data => {
          const updatedFormData = {
            name: data.Name || '',
            panNumber: data.pan_number || '',
            aadharNumber: data.aadhar_number || '',
            disbursementAmount: data.disbursement_amount || ''
          };
          setFormData(updatedFormData);
    
          // Build new URL with prefilled data
          const params = new URLSearchParams({
            name: updatedFormData.name,
            pan: updatedFormData.panNumber,
            aadhar: updatedFormData.aadharNumber,
            disbursement_amount: updatedFormData.disbursementAmount
          }).toString();
          
          const redirectUrl = encodeURIComponent("http://localhost:3000/Upload?completed=true");
          const newFormUrl = `https://form.jotform.com/251141777133049?${params}&redirect=${redirectUrl}`;
          setFormUrl(newFormUrl);
        }
      )
    }
    catch (error) {
      console.error("Error fetching autofill data:", error);
    }
  }
  };
    fetchAutofillData();
    }, [activeTab, uuid]);


      useEffect(() => {
        // in useEffect or page load
            const params = new URLSearchParams(window.location.search);
            const completed = params.get("completed") === "true";
          
            if (completed) {
              setActiveTab("Disbursement");
          
              // Optional: Clear the ?completed=true from URL
              const cleanUrl = `${window.location.origin}/Upload`;
              window.history.replaceState({}, document.title, cleanUrl);
            }
          }, []);
          useEffect(() => {
            if (activeTab === "Review Details" && formUrl.includes("?")) {
              console.log("Redirecting to JotForm with autofilled data:", formUrl);
              window.location.href = formUrl;
            }
          }, [activeTab, formUrl]);
      

 

  useEffect(() => {
    const fetchLoanDetails = async () => {
      try {
        const response = await fetch("http://localhost:8000/dropdown");
        const data = await response.json();
        setLoanDetails(data);
      } catch (error) {
        console.error("Error fetching dropdown data:", error);
      }
    };

    fetchLoanDetails();
  }, []); // you can add dependencies like riskStatus if needed

  const fetchKycVerified = async () => { // Fetch KYC verification status from backend
    try {
        const response = await axios.get(kycVerifyUrl);
        console.log(response.data)
        if (response.data[0].kyc_verified === "Yes") { // Updated condition
            setKycVerified("🎉 KYC Successful");  // Updated message
        } else {
            setKycVerified("❌ KYC Failed");  // Updated message
        }
    } catch (error) {
        setKycVerified("❌ Docs Not found");  // Handles API failure case
    }
};

useEffect(() => {
  window.history.pushState(null, "", window.location.href);
  const handlePopState = () => {
    window.history.pushState(null, "", window.location.href);
  };
  window.addEventListener("popstate", handlePopState);
  return () => {
    window.removeEventListener("popstate", handlePopState);
  };
}, []);

// endprocess after few seconds 
useEffect(() => {
  const timer = setTimeout(() => {
    setShowEndButton(true);
  }, 5000); // 5 seconds

  return () => clearTimeout(timer); // Cleanup
}, []);

useEffect(() => {
  if (activeTab === "Disbursement") {
    const storedUuid = localStorage.getItem("loanApplicationUUID");

    if (storedUuid) {
      axios.put(`http://127.0.0.1:8000/api/loan-state/${storedUuid}`, null, {
        params: { new_stage: "Disbursement" }
      })
      .then(() => {
        console.log("✅ Loan stage updated to Disbursement");
      })
      .catch((err) => {
        console.error("❌ Failed to update loan stage:", err);
      });
    } else {
      console.warn("⚠️ No UUID found in localStorage.");
    }
  }
}, [activeTab]);


  const documents = [
    { name: "PAN" },
    { name: "Aadhar" },
    { name: "Loan-Application" },
    { name: "Salary-slip" },
  ];
  const tabs = ["Upload", "KYC Agent", "Risk Assessment Agent", "Onboarding Agent", "Review Details","Disbursement"];

  return (
    <div className="upload-container">
      {/* Top section with Logout */}
          <button className="logoutbutton" onClick={() => navigate("/")}>
            <FaUser className="profile-icon" /> Logout
          </button>

      {/* Tab Navigation */}
      <div className="tab-bar">
        {tabs.map((tab) => (
          <button
            key={tab}
            className={`tab-button ${activeTab === tab ? "active" : ""}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Combined Info Box displaying User Name and UUID */}
      <div className="combined-info-box">
        <p className="combined-info-text">
          <FaUser className="login-icon" /> Loan Application Number: {storedUuid || "N/A"}
        </p>
      </div>


      {/* Tab Content */}
      <div className="tab-content">
        {activeTab === "Upload" && (
          <div className="upload-box">
            <h2>Upload Documents</h2>
            <table className="styled-table">
              <thead>
                <tr>
                  <th>Documentation</th>
                  <th>Status</th>
                  <th>Attach</th>
                  <th>Submit</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((doc, index) => (
                  <tr key={index}>
                    <td>{doc.name}</td>
                    <td>
                      <span
                        className={
                          uploadStatus[doc.name] === "success"
                            ? "submitted-badge"
                            : "required-badge"
                        }
                      >
                        {uploadStatus[doc.name] === "success"
                          ? "Submitted"
                          : "Required"}
                      </span>
                    </td>
                    <td>
                      <label className="attach-icon">
                        <input
                          type="file"
                          style={{ display: "none" }}
                          onChange={(e) => handleFileChange(e, doc.name)}
                          id={`file-input-${index}`}
                        />
                        <button
                          className="paperclip-btn"
                          onClick={(e) => {
                            e.preventDefault();
                            document.getElementById(`file-input-${index}`).click();
                          }}
                        >
                          <FaPaperclip size={11} />
                        </button>
                      </label>
                    </td>
                    <td>
                      <button className="small-submit-btn" onClick={() => handleUpload(doc.name)}>
                        Submit
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Verify Button - Positioned at the bottom left */}
            <button className="verify-button" onClick={() =>{handleVerifyClick();handleNextStep();}}>
              Next Step
            </button>          
            </div>
        )}

        {activeTab === "KYC Agent" && (
  <div className="kyc-container">
    <div className="kyc-gif-box">
      <img
        src={
          kycLoading
            ? "https://media.licdn.com/dms/image/sync/v2/D5627AQEJQN0F1uPrgw/articleshare-shrink_800/articleshare-shrink_800/0/1733051406666?e=2147483647&v=beta&t=McWWzzDupD-oTXWodo0WwogprMx1BxYFk7cngqBUvLk"
            : kycVerified === "❌ KYC Failed" || kycVerified === "❌ Docs Not found"
            ? "https://portal.maktabsoft.ir/95136081/component/messenger/assets/images/failed.gif"
            : "https://cdn.dribbble.com/userupload/15097592/file/original-11af0dab65a0913fe4ea1d71d9d48f4a.gif"
        }
        alt="KYC Process"
        className="kyc-gif"
      />
      <p className="kyc-gif-text">
        {kycLoading
          ? "Agent Is Processing"
          : kycVerified === "❌ KYC Failed" || kycVerified === "❌ Docs Not found"
          ? "Oops! Something went wrong"
          : "🎉 KYC Successful"}
        <span className="dots"></span>
      </p>
    </div>

    <div className="kyc-content">
      <h2>KYC Section</h2>
      <div className="kyc-status">
        {kycLoading ? (
          <p>
            {kycSteps.slice(0, kycStepIndex + 1).map((step, index) => (
              <span key={index}>
                {step}
                <br />
              </span>
            ))}
          </p>
        ) : (
          <p>{kycVerified}</p>
        )}
      </div>

      {kycVerified === "🎉 KYC Successful" && (
        <>
          <button className="next-button" onClick={() => {
            handleRiskAssessment();
            handleNextStep();
          }}>
            Next step
          </button>

          {/* 🎯 KYC Details Table inserted below */}
          <div className="kyc-summary-table">
            <KYCDetails />
          </div>
          {(kycVerified === "🎉 KYC Successful" || kycVerified === "❌ KYC Failed" || kycVerified === "❌ Docs Not found") && (
  <div className="card-viewer-wrapper">
    <CardViewer />
  </div>
)}

        </>
      )}

      {(kycVerified === "❌ KYC Failed" || kycVerified === "❌ Docs Not found") && (
        <button className="next-button" onClick={() => {
          handleUpload();
          handlePreviousStep();
        }}>
          Retry
        </button>
      )}
    </div>
  </div>
)}


        {/* Risk PROCESS DISPLAY */}
        {activeTab === "Risk Assessment Agent" && (
  <div className="risk-page-wrapper">
    {/* Left: Risk Container */}
    <div className="risk-container">
      <div className="kyc-gif-box">
        <img
          src={
            riskLoading
              ? "https://media.licdn.com/dms/image/sync/v2/D5627AQEJQN0F1uPrgw/articleshare-shrink_800/articleshare-shrink_800/0/1733051406666?e=2147483647&v=beta&t=McWWzzDupD-oTXWodo0WwogprMx1BxYFk7cngqBUvLk"
              : riskStatus === "❌ Risk assessment Failed" ||
                riskStatus === "❌ Agent Faced an issue"
              ? "https://portal.maktabsoft.ir/95136081/component/messenger/assets/images/failed.gif"
              : "https://cdn.dribbble.com/userupload/15097592/file/original-11af0dab65a0913fe4ea1d71d9d48f4a.gif"
          }
          alt="KYC Process"
          className="kyc-gif"
        />
        <p className="kyc-gif-text">
          {riskLoading
            ? "Agent Is Processing"
            : riskStatus === "❌ Risk assessment Failed" ||
              riskStatus === "❌ Agent Faced an issue"
            ? "Oops! Something went wrong"
            : "🎉 Risk Assessment Successful"}
          <span className="dots"></span>
        </p>
      </div>

      <div className="risk-section">
        <div className="risk-header">
        {(riskStatus === "❌ Customer is not Eligible for Loan" || riskStatus === "🎉 Customer is Eligible for Loan") &&(<p className="eligblity-score">Score: {loanScore}/10</p>)}
        <h2 className="risk-box">Risk Assessment Section</h2>
        </div>
        <div className="risk-status">
          {riskLoading ? (
            <p>
              {riskSteps.slice(0, riskStepIndex + 1).map((step, index) => (
                <span key={index}>
                  {step}
                  <br />
                </span>
              ))}
            </p>
          ) : (
            <p>{riskStatus}</p>
          )}
        </div>
        {(riskStatus === "❌ Customer is not Eligible for Loan" || riskStatus === "🎉 Customer is Eligible for Loan") && <EmailPreview emailData={loanDetails} />}

        {riskStatus === "🎉 Customer is Eligible for Loan" && (
          <>
            <button
              className="approve-button"
              onClick={() => {
                updateLoanStage("Onboarding Agent", "Approved");
                handleonboarding();
                handleNextStep();
              }}
            >
              Approve
            </button>
            <button
              className="reject-button"
              onClick={() => {
                updateLoanStage("Upload", "Rejected");
                handleUpload();
                handlerejection();
              }}
            >
              Reject
            </button>
          </>
         )}


        {riskStatus === "❌ Customer is not Eligible for Loan" && (
          <>
            <button
              className="approve-button"
              disabled = {true}
              onClick={() => {handleonboarding();
                handleNextStep();
              }}
            >
              Approve
            </button>
            <button
              className="reject-button"
              onClick={() => {
                updateLoanStage("Upload", "Rejected");
                handleUpload();
                handlerejection();
              }}>
              Reject
            </button>
          </>
        )}

      </div>
    </div>

    {/* Right: Dropdown Sidebar */}
    {loanDetails && (
  <LoanRiskDropdown
    riskStatus={riskStatus}
    loanDetails={loanDetails}
  />
)}
  </div>
)}

 {/* Review Details Tab: Use the dynamically built formUrl */}
 {activeTab === "Review Details" && (
  <div className="review-details-container">
    <h2>Review Details</h2>
    <p>You will be redirected to JotForm to complete your review.</p>
  </div>
)}

        {activeTab === "Onboarding Agent" && <OnboardingTab />}
      </div>
        {activeTab === "Onboarding Agent" && <OnboardingTab /> && (
    <div>
      <button
        className="proceed-button"
        onClick={() => {
          setActiveTab("Review Details");
          handleNextStep();

          // Wait 50ms to let state update (optional but safer)
          setTimeout(() => {
            if (formUrl && formUrl.includes("?")) {
              console.log("Redirecting to:", formUrl);
              window.location.href = formUrl;
            } else {
              console.warn("Form URL not ready yet.");
            }
          }, 0);
        }}
      >
        Proceed
      </button>
  </div>
      )}
  {activeTab === "Disbursement" && (
  <>
    <Disbursement />
    <div>
    {showEndButton && (
  <button className="end-process-button" onClick={handleEndProcess}>
    End Process
  </button>
)}
    </div>
  </>
)}


    </div>
  );
};


export default Upload;

