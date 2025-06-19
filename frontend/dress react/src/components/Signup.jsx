import React, { useState } from 'react';
import './Signup.css';


export default function Signup() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');

  const handleSignup = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch('http://localhost:5000/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json();
      setMessage(res.ok ? 'Signup successful!' : data.error);
    } catch (err) {
      setMessage('Network error');
    }
  };

  return (
    <form onSubmit={handleSignup}>
      <h2>Signup</h2>
      <input placeholder="Username" value={username} onChange={e => setUsername(e.target.value)} required />
      <br />
      <input type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} required />
      <br />
      <button type="submit">Signup</button>
      <p>{message}</p>
    </form>
  );
}
