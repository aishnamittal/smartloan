import React, { useState, useEffect } from 'react';
import './LoanRiskDropdown.css';

function LoanRiskDropdown({ riskStatus }) {
  const [selectedDropdown, setSelectedDropdown] = useState(null);
  const [loanDetails, setLoanDetails] = useState(null);

  const toggleDropdown = (key) => {
    setSelectedDropdown(prev => (prev === key ? null : key));
  };

  // 🔽 Fetch data from /dropdown on component mount
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
  }, []);


  const isEligible =
    riskStatus === "❌ Customer is not Eligible for Loan" ||
    riskStatus === "🎉 Customer is Eligible for Loan";

  if (!isEligible || !loanDetails) return null;

  return (
    <div className="risk-dropdown-container">
      {[
        {
          key: 'cibil',
          title: '▸ CIBIL Analysis',
          content: <p>💳 Credit Score: {loanDetails.credit_score}</p>
        },
        {
          key: 'loans',
          title: '▸ Previous Loans',
          content: <p>🔄 Delinquency History: {loanDetails.delinquency_history} Delinquency</p>
        },
        {
          key: 'eligibility',
          title: '▸ Loan Amount',
          content: <p>📄 Loan Amount: {loanDetails.loan_amount}</p>
        },
        {
          key: 'income',
          title: '▸ Summary',
          content: (
            <>
              <p>💳 The customer has a credit score of <strong>{loanDetails.credit_score}</strong> and has applied for a <br></br><strong>{loanDetails.loan_type}</strong> loan of ₹<strong>{loanDetails.loan_amount}</strong>.</p>
              <p>💼 Their net monthly income is ₹<strong>{loanDetails.Net_Monthly_Income}</strong>, with <strong>{loanDetails.delinquency_history}</strong> past delinquency(s) on record.</p>
            </>
          )
        }
      ].map(item => (
        <div key={item.key} className="custom-dropdown">
          <button
            className="custom-dropdown-toggle"
            onClick={() => toggleDropdown(item.key)}
          >
            {item.title}
          </button>
          <div className={`custom-dropdown-content ${selectedDropdown === item.key ? 'show' : ''}`}>
            {item.content}
          </div>
        </div>
      ))}
    </div>
  );
}

export default LoanRiskDropdown;
// import React, { useState, useEffect } from 'react';
// import './LoanRiskDropdown.css';

// function LoanRiskDropdown({ riskStatus }) {
//   const [selectedDropdown, setSelectedDropdown] = useState(null);
//   const [loanDetails, setLoanDetails] = useState(null);
//   const [riskAssessment, setRiskAssessment] = useState(null); // ⬅️ New state

//   const toggleDropdown = (key) => {
//     setSelectedDropdown(prev => (prev === key ? null : key));
//   };

//   // 🔽 Fetch loan dropdown details
//   useEffect(() => {
//     const fetchLoanDetails = async () => {
//       try {
//         const response = await fetch("http://localhost:8000/dropdown");
//         const data = await response.json();
//         setLoanDetails(data);
//       } catch (error) {
//         console.error("Error fetching dropdown data:", error);
//       }
//     };

//     fetchLoanDetails();
//   }, []);

//   // 🔽 Fetch full risk assessment
//   useEffect(() => {
//     const fetchRiskAssessment = async () => {
//       try {
//         const response = await fetch("http://localhost:8000/risk-assessment/");
//         const data = await response.json();
//         setRiskAssessment(data);
//       } catch (error) {
//         console.error("Error fetching risk assessment:", error);
//       }
//     };

//     fetchRiskAssessment();
//   }, []);

//   const isEligible =
//     riskStatus === "❌ Customer is not Eligible for Loan" ||
//     riskStatus === "🎉 Customer is Eligible for Loan";

//   if (!isEligible || !loanDetails) return null;

//   return (
//     <div className="risk-dropdown-container">
//       {[
//         {
//           key: 'cibil',
//           title: '▸ CIBIL Analysis',
//           content: <p>💳 Credit Score: {loanDetails.credit_score}</p>
//         },
//         {
//           key: 'loans',
//           title: '▸ Previous Loans',
//           content: <p>🔄 Delinquency History: {loanDetails.delinquency_history} Delinquency</p>
//         },
//         {
//           key: 'eligibility',
//           title: '▸ Loan Amount',
//           content: <p>📄 Loan Amount: {loanDetails.loan_amount}</p>
//         },
//         {
//           key: 'income',
//           title: '▸ Summary',
//           content: (
//             <>
//               <p>📄 Salary Slip Verified: {loanDetails.salary_slip_verified ? "❌ No" : "✅ Yes"}</p>
//               {riskAssessment && (
//                 <>
//                   <p>✉️ Email Preview:</p>
//                   <pre className="email-preview">
//                     {riskAssessment.email_content
//                       .split('\n')
//                       .slice(0, 2)
//                       .join('\n')}
//                   </pre>
//                 </>
//               )}
//             </>
//           )
//         }
//       ].map(item => (
//         <div key={item.key} className="custom-dropdown">
//           <button
//             className="custom-dropdown-toggle"
//             onClick={() => toggleDropdown(item.key)}
//           >
//             {item.title}
//           </button>
//           <div className={`custom-dropdown-content ${selectedDropdown === item.key ? 'show' : ''}`}>
//             {item.content}
//           </div>
//         </div>
//       ))}
//     </div>
//   );
// }

// export default LoanRiskDropdown;
