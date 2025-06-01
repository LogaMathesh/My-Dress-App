import React, { useState } from "react";
import axios from "axios";
import { useNavigate, Link } from "react-router-dom";

function Signup({ onLogin }) {
  const [form, setForm] = useState({ username: "", password: "" });
  const [error, setError] = useState("");
  const navigate = useNavigate();

  // Handle input field changes
  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  // Handle form submission for signup
  const handleSignup = async (e) => {
    e.preventDefault();
    try {
      // Send POST request to signup endpoint
      const res = await axios.post("http://localhost:5000/signup", form, {
        headers: {
          "Content-Type": "application/json",
        },
      });

      // If signup is successful
      if (res.status === 200 || res.status === 201) {
        alert(res.data.message); // Show success message
        onLogin(); // Inform parent component that user is logged in
        navigate("/upload"); // Redirect to upload page
      }
    } catch (err) {
      console.error("Signup error:", err);
      console.error("Error response:", err.response);
      setError(err.response?.data?.message || "Signup failed"); // Show error message if signup fails
    }
  };

  return (
    <div>
      <h2>Sign Up</h2>
      <form onSubmit={handleSignup}>
        <input
          name="username"
          onChange={handleChange}
          placeholder="Username"
          required
        />
        <input
          name="password"
          type="password"
          onChange={handleChange}
          placeholder="Password"
          required
        />
        <button type="submit">Sign Up</button>
      </form>
      {error && <p style={{ color: "red" }}>{error}</p>} {/* Show error message */}
      <p>
        Already have an account? <Link to="/signin">Sign in</Link> {/* Link to Sign In */}
      </p>
    </div>
  );
}

export default Signup;
