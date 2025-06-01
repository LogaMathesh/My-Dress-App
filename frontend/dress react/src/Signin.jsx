import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

function Signin({ onLogin }) {
  const [form, setForm] = useState({ username: "", password: "" });
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSignin = async (e) => {
    e.preventDefault();
    setError(""); // Clear previous errors

    try {
      const res = await axios.post("http://localhost:5000/signin", form);
      
      if (res.data.message === "Login successful") {
        alert("Login successful");
        onLogin(); // Inform App that user is logged in
        navigate("/upload"); // Redirect to upload page
      } else {
        setError("Invalid credentials. Please try again.");
      }
    } catch (err) {
      console.error("Login error:", err);
      setError(err.response?.data?.message || "Login failed. Please try again.");
    }
  };

  return (
    <div>
      <h2>Sign In</h2>
      <form onSubmit={handleSignin}>
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
        <button type="submit">Sign In</button>
      </form>
      {error && <p style={{ color: "red" }}>{error}</p>}
    </div>
  );
}

export default Signin;
