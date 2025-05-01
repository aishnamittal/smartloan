import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Login from "./pages/Login";
import Upload from "./pages/Upload";
import Dashboard from "./pages/dashboard";
import Disbursement from "./pages/Disbursement";
import axios from "axios";
import KYCDetails from "./pages/KYCDetails";
import Onboarding from "./pages/onboarding";


const token = localStorage.getItem("token");
if (token) {
  axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/upload" element={<Upload />} />
        {/* <Route path="/disbursement" element={<Disbursement />} /> */}
        <Route path="/KYCDetails" element={<KYCDetails  />} />
        {/* <Route path="/onboarding" element={<Onboarding />} /> */}
      </Routes>
    </Router>
  );
}

export default App;