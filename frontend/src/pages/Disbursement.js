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
        <h2 className="disb">Loan Disbursement</h2>
      </div>

      {loanDetails && (
        <table className="loan-table">
          <thead>
            <tr>
              <th>Field</th>
              <th>Value</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>Applicant Name</strong></td>
              <td>{loanDetails.applicant_name}</td>
            </tr>
            <tr>
              <td><strong>Application Number</strong></td>
              <td>{loanDetails.application_number}</td>
            </tr>
            <tr>
              <td><strong>Loan Amount</strong></td>
              <td>{loanDetails.loan_amount}</td>
            </tr>
            <tr>
              <td><strong>Disbursed Amount</strong></td>
              <td>{loanDetails.disbursed_amount}</td>
            </tr>
            <tr>
              <td><strong>Remaining Amount</strong></td>
              <td>{loanDetails.remaining_amount}</td>
            </tr>
            <tr>
              <td><strong>Status</strong></td>
              <td>{loanDetails.disbursement_status}</td>
            </tr>
          </tbody>
        </table>
      )}

      {error && <p className="error-message">❌ {error}</p>}
    </div>
  );
};

export default Disbursement;
