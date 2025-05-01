
// import React, { useEffect, useState } from "react";
// import axios from "axios";
// import "./KYCDetails.css";
// import { Pencil } from "lucide-react";

// const KYCDetails = () => {
//   const [kycData, setKycData] = useState({});
//   const [editableRows, setEditableRows] = useState({}); // Track edit state per row

//   useEffect(() => {
//     axios
//       .get("http://localhost:8000/kyc-details/")
//       .then((res) => {
//         setKycData(res.data);
//       })
//       .catch((err) => {
//         console.error("Failed to fetch KYC data", err);
//       });
//   }, []);

//   const combinedEntries = [];

//   Object.entries(kycData).forEach(([_, details]) => {
//     if (details.pan_number)
//       combinedEntries.push(["PAN Number", details.pan_number.value, details.pan_number.confidence]);

//     if (details.aadhar_number)
//       combinedEntries.push(["Aadhar Number", details.aadhar_number.value, details.aadhar_number.confidence]);

//     if (details.name)
//       combinedEntries.push(["Name", details.name.value, details.name.confidence]);

//     if (details.dob)
//       combinedEntries.push(["Date of Birth", details.dob.value, details.dob.confidence]);
//   });

//   const toggleEdit = (index) => {
//     setEditableRows((prev) => ({ ...prev, [index]: !prev[index] }));
//   };

//   return (
//     <div className="kyctable-container">
//       <h2 className="kyc-heading">KYC Summary Table</h2>

//       <table className="kyc-table-vertical">
//         <thead>
//           <tr>
//             <th>Entry</th>
//             <th>Value</th>
//             <th>Confidence Score</th>
//           </tr>
//         </thead>
//         <tbody>
//           {combinedEntries.map(([label, value, confidence], index) => {
//             const confidenceColor =
//               typeof confidence === "number" && confidence < 85
//                 ? "low-confidence"
//                 : "high-confidence";

//             const isLowConfidence = typeof confidence === "number" && confidence < 85;
//             const isEditing = editableRows[index];

//             return (
//               <tr key={`${label}-${index}`}>
//                 <td className="entry-col">{label}</td>
//                 <td>
//                   {isLowConfidence && isEditing ? (
//                     <input
//                       type="text"
//                       defaultValue={value}
//                       className="edit-input"
//                       onChange={(e) => {
//                         combinedEntries[index][1] = e.target.value;
//                       }}
//                     />
//                   ) : (
//                     value || "-"
//                   )}
//                   {isLowConfidence && (
//                     <span onClick={() => toggleEdit(index)} className="edit-icon">
//                     <Pencil size={16} style={{ cursor: "pointer" }} />
//                     </span>
//                   )}

//                 </td>
//                 <td className={confidenceColor}>
//                   {typeof confidence === "number" ? confidence.toFixed(2) : "-"}
//                 </td>
//               </tr>
//             );
//           })}
//         </tbody>
//       </table>
//     </div>
//   );
// };

// export default KYCDetails;
import React, { useEffect, useState } from "react";
import axios from "axios";
import "./KYCDetails.css";
import { Pencil } from "lucide-react";

const KYCDetails = () => {
  const [kycData, setKycData] = useState({});
  const [editableRows, setEditableRows] = useState({});
  const [editedValues, setEditedValues] = useState({});

  useEffect(() => {
    axios
      .get("http://localhost:8000/kyc-details/")
      .then((res) => {
        setKycData(res.data);
      })
      .catch((err) => {
        console.error("Failed to fetch KYC data", err);
      });
  }, []);

  const combinedEntries = [];

  Object.entries(kycData).forEach(([_, details]) => {
    if (details.pan_number)
      combinedEntries.push(["PAN Number", details.pan_number.value, details.pan_number.confidence]);

    if (details.aadhar_number)
      combinedEntries.push(["Aadhar Number", details.aadhar_number.value, details.aadhar_number.confidence]);

    if (details.name)
      combinedEntries.push(["Name", details.name.value, details.name.confidence]);

    if (details.dob)
      combinedEntries.push(["Date of Birth", details.dob.value, details.dob.confidence]);
  });

  const toggleEdit = (index) => {
    setEditableRows((prev) => ({ ...prev, [index]: !prev[index] }));
    if (!editableRows[index]) {
      setEditedValues((prev) => ({ ...prev, [index]: combinedEntries[index][1] }));
    }
  };

  const handleInputChange = (index, newValue) => {
    setEditedValues((prev) => ({ ...prev, [index]: newValue }));
  };

  return (
    <div className="kyctable-container">
      <h2 className="kyc-heading">KYC Summary Table</h2>

      <table className="kyc-table-vertical">
        <thead>
          <tr>
            <th>Entry</th>
            <th>Value</th>
            <th>Confidence Score</th>
          </tr>
        </thead>
        <tbody>
          {combinedEntries.map(([label, value, confidence], index) => {
            const confidenceColor =
              typeof confidence === "number" && confidence < 85
                ? "low-confidence"
                : "high-confidence";

            const isLowConfidence = typeof confidence === "number" && confidence < 85;
            const isEditing = editableRows[index];
            const displayValue = editedValues[index] ?? value;

            return (
              <tr key={`${label}-${index}`}>
                <td className="entry-col">{label}</td>
                <td>
                  {isLowConfidence && isEditing ? (
                    <input
                      type="text"
                      value={displayValue}
                      className="edit-input"
                      onChange={(e) => handleInputChange(index, e.target.value)}
                      onBlur={() => toggleEdit(index)}
                      autoFocus
                    />
                  ) : (
                    <>
                      {displayValue || "-"}
                      {isLowConfidence && (
                        <span onClick={() => toggleEdit(index)} className="edit-icon">
                          <Pencil size={16} style={{ cursor: "pointer", marginLeft: "10px" }} />
                        </span>
                      )}
                    </>
                  )}
                </td>
                <td className={confidenceColor}>
                  {typeof confidence === "number" ? confidence.toFixed(2) : "-"}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

export default KYCDetails;
