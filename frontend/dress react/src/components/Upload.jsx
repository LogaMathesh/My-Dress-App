import React, { useState } from 'react';
import './upload.css';

export default function Upload({ username }) {
  const [image, setImage] = useState(null);
  const [result, setResult] = useState(null);
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);  // <-- Loading state added

  const handleUpload = async (e) => {
    e.preventDefault();
    setMessage('');
    if (!image) return setMessage('Please select an image.');

    const formData = new FormData();
    formData.append('image', image);
    formData.append('username', username);

    setIsLoading(true);  // Start loading

    try {
      const res = await fetch('http://localhost:5000/classify', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      setResult(data);
      setMessage('Classification successful!');
    } catch {
      setMessage('Upload failed');
      setResult(null);
    } finally {
      setIsLoading(false);  // Stop loading
    }
  };

  return (
    <div className="upload-container">
      <h2>Upload and Classify Image</h2>
      <form onSubmit={handleUpload}>
        <input
          type="file"
          onChange={e => setImage(e.target.files[0])}
          required
          disabled={isLoading}  // Disable input while loading
        />
        <button type="submit" disabled={isLoading}>
          {isLoading ? 'Classifying...' : 'Classify'}
        </button>
      </form>

      {/* Loading spinner */}
      {isLoading && (
        <div className="spinner-container">
          <div className="spinner" />
          <p>Classifying image, please wait...</p>
        </div>
      )}

      {/* Display result only if not loading */}
      {!isLoading && result && (
        <div>
          <h3>Results:</h3>
          <p><strong>Position:</strong> {result.position}</p>
          <p><strong>Style:</strong> {result.style}</p>
          <p><strong>Color:</strong> {result.color}</p>
          <img src={result.image_url} alt="Classified" width="200" />
        </div>
      )}

      <p>{message}</p>

      {/* CSS spinner styles */}
      <style>{`
        .spinner-container {
          margin-top: 20px;
          text-align: center;
        }
        .spinner {
          margin: 0 auto 10px auto;
          width: 40px;
          height: 40px;
          border: 4px solid rgba(0,0,0,0.1);
          border-left-color: #09f;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
