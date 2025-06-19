import React, { useState } from 'react';

export default function Suggestions() {
  const [destination, setDestination] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [message, setMessage] = useState('');

  const fetchSuggestions = async () => {
    try {
      const res = await fetch('http://localhost:5000/get-suggestions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ destination })
      });

      const data = await res.json();

      if (data.suggestions.length === 0) {
        setMessage('No matching dresses found.');
        setSuggestions([]);
      } else {
        setSuggestions(data.suggestions);
        setMessage('');
      }
    } catch (err) {
      console.error('Error fetching suggestions:', err);
      setMessage('Failed to fetch suggestions. Try again.');
    }
  };

  return (
    <div className="suggestions">
      <h2>Dress Suggestions</h2>
      
      <label>Select your destination:</label>
      <select value={destination} onChange={(e) => setDestination(e.target.value)}>
        <option value="">--Select--</option>
        <option value="beach">Beach</option>
        <option value="casual">Casual</option>
        <option value="formal">Formal</option>
        <option value="traditional">Traditional</option>
      </select>

      <button onClick={fetchSuggestions} disabled={!destination}>
        Show Suggestions
      </button>

      {message && <p>{message}</p>}

      <div className="suggestion-grid">
        {suggestions.map((item, index) => (
          <div key={index} className="suggestion-card">
            <img
              src={`http://localhost:5000/${item.image_path}`}
              alt="Dress"
              width="200"
              onError={(e) => { e.target.src = '/placeholder.png'; }} // Optional fallback
            />
            <p><strong>Style:</strong> {item.style}</p>
            <p><strong>Uploaded At:</strong> {new Date(item.uploaded_at).toLocaleString()}</p>
            <p><strong>Position:</strong> {item.position}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
