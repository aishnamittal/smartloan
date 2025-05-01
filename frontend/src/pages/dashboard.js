import React, { useEffect, useState } from "react";
import axios from "axios";
import { useLocation } from "react-router-dom";
import { useNavigate } from "react-router-dom";
import { FaPaperclip } from "react-icons/fa"; // Importing paperclip icon
import { FaFileUpload, FaUserCircle } from "react-icons/fa";
import "./dashboard.css";

const Dashboard = () => {
  const location = useLocation();
  const [loanApplications, setLoanApplications] = useState([]);
  const [selectedLoan, setSelectedLoan] = useState(null);
  const [files, setFiles] = useState({});
  const [showProfileDropdown, setShowProfileDropdown] = useState(false);
  const [uploadStatus, setUploadStatus] = useState({});
  const [showDashboardIframe, setShowDashboardIframe] = useState(false);
  const [showNewDropdown, setShowNewDropdown] = useState(false);
  const [showCompletedDropdown, setShowCompletedDropdown] = useState(false);
  const [userProfile, setUserProfile] = useState(null);
  const navigate = useNavigate();

  const stages = ["Upload", "KYC", "Risk Assessment", "Onboarding","Review Details", "Disbursement"];



  const handleFileChange = (e, docType) => {
    setFiles({ ...files, [docType]: e.target.files[0] });
  };

  const handleUpload = (docType) => {
    if (!files[docType]) {
      alert("Please select a file before uploading.");
      return;
    }

    setUploadStatus({ ...uploadStatus, [docType]: "success" });
    alert(`${docType} uploaded successfully for Loan #${selectedLoan}!`);
  };

  const updateLoanStage = async (loanApplicationNumber, newStage) => {
    try {
        await axios.put(`http://127.0.0.1:8000/api/loan-state/${loanApplicationNumber}`, {
            stage: newStage
        });
    } catch (error) {
        console.error("Error updating loan stage:", error);
    }
};


// Example: Move to the next stage
const moveToNextStage = (loanApplicationNumber, currentStage) => {
    const nextStageIndex = stages.indexOf(currentStage) + 1;
    if (nextStageIndex < stages.length) {
        const nextStage = stages[nextStageIndex];
        updateLoanStage(loanApplicationNumber, nextStage);
    }
};


useEffect(() => {
  window.history.pushState(null, "", window.location.href);
  const handlePopState = () => {
    window.history.pushState(null, "", window.location.href);
  };
  window.addEventListener("popstate", handlePopState);
  return () => window.removeEventListener("popstate", handlePopState);
}, [location, navigate]);


useEffect(() => {
  const fetchLoans = async () => {
    try {
      const response = await axios.get("http://127.0.0.1:8000/api/loan-state");
      setLoanApplications(response.data);
    } catch (error) {
      console.error("Error fetching loan applications:", error);
    }
  };

  fetchLoans();
}, []);
useEffect(() => {
  const fetchUserProfile = async () => {
    try {
      const token = localStorage.getItem("access_token"); // Or however you store it
      const response = await axios.get("http://127.0.0.1:8000/api/profile", {
        headers: {
          Authorization:` Bearer ${token}`,
        },
      });
      setUserProfile(response.data);
    } catch (err) {
      console.error("Failed to fetch user profile", err);
    }
  };

  fetchUserProfile();
}, []);
const normalizeStage = (stage) => {
  if (stage.includes("Upload")) return "Upload";
  if (stage.includes("KYC")) return "KYC";
  if (stage.includes("Risk")) return "Risk Assessment";
  if (stage.includes("Onboarding")) return "Onboarding";
  if (stage.includes("Disbursement")) return "Disbursement";
  if (stage.includes("Review")) return "Review Details"
  return ""; // fallback
};

const getProgress = (stage) => {
  const normalizedStage = normalizeStage(stage);
  const index = stages.indexOf(normalizedStage);
  return index >= 0 ? Math.round(((index + 1) / stages.length) * 100) : 0;
};
const completedLoans = loanApplications.filter(
  (loan) => getProgress(loan.stage) === 100
);

const inProgressLoans = loanApplications.filter(
  (loan) => getProgress(loan.stage) < 100
);


const handleLoanClick = (loan) => {
  navigate("/Upload", {
    state: {
      uuid: loan.loanApplicationNumber,
      activeTab: loan.stage
    }
  });
};

  return (
    <div className="dashboard-container">
      {/* Top Bar */}
      <div className="top-bar">
        {/* Logo on the Left */}
        <div className="logo-container">
          <img
            src="https://www.ey.com/content/dam/ey-unified-site/ey-com/en-gl/generic/images/ey-logo-black.png"
            alt="Company Logo"
          />
        </div>

        {/* Centered Header Items */}
        <div className="center-header">
          <div className="dropdown">
            <button
              onClick={() => setShowNewDropdown(!showNewDropdown)}
              className="dropdown-btn"
            >
              New ▼
            </button>
            {showNewDropdown && (
              <div className="dropdown-content">
                <button
                  className="dropdown-item"
                  onClick={() => navigate("/Upload")}
                >
                  Create LAN
                </button>
              </div>
            )}
          </div>

          <div className="dropdown">
            <button
              onClick={() => setShowCompletedDropdown(!showCompletedDropdown)}
              className="dropdown-btn"
            >
              Completed ▼
            </button>
            {showCompletedDropdown && (
              <div className="dropdown-content">
                {completedLoans.map((loan) => (
              <button
                key={loan.loanApplicationNumber || loan}
                className="dropdown-item"
                onClick={() => {
                  navigate("/Upload", {
                    state: {
                      uuid: loan.loanApplicationNumber || loan,
                      activeTab: "Disbursement",
                    },
                  });
                  setShowCompletedDropdown(false); // this closes the dropdown
                }}
              >
                Loan #{loan.loanApplicationNumber || loan}
              </button>
            ))}


              </div>
            )}
          </div>
          
          <div className="dropdown">
          <button
            className="dropdown-btn"
            onClick={() => setShowDashboardIframe(!showDashboardIframe)}
          >
            Dashboard
          </button>
        </div>

        </div>

        {/* Profile Icon on the Right - Updated to navigate to Login */}
        <div className="profile-dropdown-container">
  <button
    className="profile-btn"
    onClick={() => setShowProfileDropdown(!showProfileDropdown)}
  >
    <img
          src="https://www.w3schools.com/howto/img_avatar.png"
          alt="Avatar"
          className="profile-avatar-button"
        />
  </button>

  {showProfileDropdown && (
    <div className="profile-card-dropdown">
      <div className="profile-card">
        <img
          src="https://www.w3schools.com/howto/img_avatar.png"
          alt="Avatar"
          className="profile-avatar"
        />
        <div className="profile-info">
          <h3>{userProfile?.name || "Loading..."}</h3>
          <p>{userProfile?.email}</p>
          <p>{userProfile?.phone}</p>
        </div>
        <button
          className="logout-button"
          onClick={() => {
            localStorage.removeItem("access_token"); // optional
            navigate("/");
                }}
              >
                Log Out
              </button>
            </div>
          </div>
        )}
      </div>


      </div>

      {/* Main Content - Two Column Layout */}
      <div className="main-content">
        <div className="sidebar">
        <h2>Loan Applications</h2>
        {inProgressLoans.map((loan) => (
        <div
          key={loan.loanApplicationNumber}
          className="loan-item-container"
          onClick={() => handleLoanClick(loan)}
          style={{ cursor: "pointer" }}
        >
          <button className="loan-item">
            Loan #{loan.loanApplicationNumber}
          </button>
          <div className="progress-bar">
            <div
              className="progress"
              style={{ width: `${getProgress(loan.stage)}%` }}
            ></div>
          </div>
          <span className="progress-text">{getProgress(loan.stage)}%</span>
        </div>
      ))}

        </div>
        {showDashboardIframe && (
  <div className="dashboard-iframe-container" style={{ marginTop: "20px" }}>
    <iframe
      title="PowerBI Dashboard"
      width="100%"
      height="600"
      src="https://app.powerbi.com/reportEmbed?reportId=842cf6d4-f416-4c36-8ca3-030de69b622a&autoAuth=true&ctid=29bebd42-f1ff-4c3d-9688-067e3460dc1f"
      frameBorder="0"
      allowFullScreen={true}
    />
  </div>
)}

        {/* <div className="top-right-profile">
          <div className="profile-card">
            <img
              src="https://www.w3schools.com/howto/img_avatar.png"
              alt="Avatar"
              className="profile-avatar"
            />
            <div className="profile-info">
            <h3>{userProfile?.name || "Loading..."}</h3>
            <p>{userProfile?.email}</p>
            <p>{userProfile?.phone}</p>
            </div>
          </div>
        </div> */}

      </div>
    </div>
  );
};

export default Dashboard;
