import React, { useState, useEffect } from 'react';

function LoanAssessment() {
  const [panNumber, setPanNumber] = useState('');
  const [loanAmount, setLoanAmount] = useState('');
  const [loanScore, setLoanScore] = useState(null);
  const [status, setStatus] = useState('');
  const [message, setMessage] = useState('');
  const [approvalDecision, setApprovalDecision] = useState('');

  // Fetch PAN and loan amount automatically on component mount
  useEffect(() => {
    const fetchLoanDetails = async () => {
      try {
        const response = await fetch('/fetch_loan_details');  // Replace with your actual endpoint
        if (response.ok) {
          const data = await response.json();
          setPanNumber(data.pan_number);
          setLoanAmount(data.loan_amount);
        } else {
          throw new Error('Failed to fetch loan details');
        }
      } catch (error) {
        console.error('Error fetching loan details:', error);
      }
    };

    fetchLoanDetails();
  }, []); // This runs only once when the component mounts

  // Function to submit the loan assessment automatically once details are fetched
  useEffect(() => {
    if (panNumber && loanAmount) {
      const fetchLoanAssessment = async () => {
        try {
          const response = await fetch('/loan_assessment/', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ pan_number: panNumber, loan_amount: loanAmount }),
          });

          if (response.ok) {
            const data = await response.json();
            setLoanScore(data.loan_score);
            setStatus(data.status);
            setMessage(data.message);
            setApprovalDecision(data.approval_decision);
          } else {
            throw new Error('Failed to fetch loan assessment');
          }
        } catch (error) {
          console.error('Error fetching loan assessment:', error);
        }
      };

      fetchLoanAssessment();
    }
  }, [panNumber, loanAmount]); // Runs when panNumber or loanAmount are updated

  return (
    <div>
      <h1>Loan Assessment</h1>
      {!loanScore ? (
        <p>Loading loan assessment...</p>
      ) : (
        <div>
          <h3>Loan Assessment Result</h3>
          <p>Loan Score: {loanScore}</p>
          <p>Status: {status}</p>
          <p>Message: {message}</p>
          <p>Approval Decision: {approvalDecision}</p>
        </div>
      )}
    </div>
  );
}

export default LoanAssessment;
