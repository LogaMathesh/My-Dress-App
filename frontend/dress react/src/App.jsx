import React, { useState } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import Signup from "./Signup";
import Signin from "./Signin";
import UploadImage from "./UploadImage";
import LandingPage from './LandingPage';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  // handleLogin function sets the user as logged in
  const handleLogin = () => {
    setIsLoggedIn(true);
  };

  return (
    <Router>
      <div>
        <h1>Fashion Classifier</h1>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route
            path="/signin"
            element={<Signin onLogin={handleLogin} />} // Passing onLogin to Signin
          />
          <Route
            path="/signup"
            element={<Signup onLogin={handleLogin} />} // Passing onLogin to Signup
          />
          <Route
            path="/upload"
            element={
              isLoggedIn ? <UploadImage /> : <Navigate to="/signin" />
            }
          />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
