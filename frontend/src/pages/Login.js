import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";  // Import Axios for API calls
import "./Login.css";

const Login = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loginError, setLoginError] = useState("");
  const [username, setUsername] = useState("");


  // Function to handle login API call
  const handleLogin = async (e) => {
    e.preventDefault();
  
    try {
      const formData = new URLSearchParams();
      formData.append("username", username);
      formData.append("password", password);
  
      const response = await axios.post("http://127.0.0.1:8000/login/", formData, {
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
      });
  
      const token = response.data.access_token;
      localStorage.setItem("access_token", token);
  
      navigate("/dashboard");
    } catch (error) {
      console.error("Login failed:", error.response?.data || error.message);
    }
  };
  
  
  return (
    <div className="login-container">
      <video autoPlay loop muted className="video-bg">
        <source src="/videos/ey.mp4" type="video/mp4" />
      </video>

      <div className="login-box">
        <img src="https://www.pngall.com/wp-content/uploads/15/EY-Logo-No-Background-180x180.png" alt="Logo" className="logo" />
        <h2>Sign In</h2>
        <input type="email" placeholder="username" value={username} onChange={(e) => setUsername(e.target.value)} />
        <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
        {/* Error Message Below Password Field */}
        {loginError && <p className="error-message">{loginError}</p>}
        <button onClick={handleLogin}>Login</button>
      </div>
    </div>
  );
};

export default Login;
