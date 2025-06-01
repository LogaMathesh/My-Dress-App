import React from 'react';
import { useNavigate } from 'react-router-dom';

function LandingPage() {
  const navigate = useNavigate();

  return (
    <div style={{ textAlign: 'center', marginTop: '50px' }}>
      <h1>Welcome to Fashion Classifier</h1>
      <p>Please choose an option to continue:</p>
      <div style={{ display: 'flex', justifyContent: 'center', gap: '20px' }}>
        <button onClick={() => navigate('/signin')}>Sign In</button>
        <button onClick={() => navigate('/signup')}>Sign Up</button>
      </div>
    </div>
  );
}

export default LandingPage;
