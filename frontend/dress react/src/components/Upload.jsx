import React, { useState } from 'react';
import './Upload.css';

export default function Upload({ username }) {
  const [image, setImage] = useState(null);
  const [previewUrl, setPreviewUrl] = useState('');
  const [result, setResult] = useState(null);
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleUpload = async (e) => {
    e.preventDefault();
    setMessage('');
    if (!image) return setMessage('Please select an image.');

    const formData = new FormData();
    formData.append('image', image);
    formData.append('username', username);

    setIsLoading(true);

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
      setIsLoading(false);
    }
  };

  return (
    <div className="upload-container">
      <h2>Upload Your Outfit</h2>
      <form onSubmit={handleUpload}>
        <input
          type="file"
          accept="image/*"
          onChange={e => {
            const file = e.target.files[0];
            setImage(file);
            setResult(null);
            if (file) {
              const url = URL.createObjectURL(file);
              setPreviewUrl(url);
            } else {
              setPreviewUrl('');
            }
          }}
          required
          disabled={isLoading}
        />
        <button type="submit" disabled={isLoading}>
          {isLoading ? 'Analyzing...' : 'Analyze Outfit'}
        </button>
      </form>

      {/* Loading spinner */}
      {isLoading && (
        <div className="spinner-container">
          <div className="spinner" />
          <p>Analyzing your outfit, please wait...</p>
        </div>
      )}

      {/* Local preview before upload */}
      {!isLoading && previewUrl && !result && (
        <div className="results">
          <h3>Preview</h3>
          <img src={previewUrl} alt="Selected preview" />
        </div>
      )}

      {/* Display result only if not loading */}
      {!isLoading && result && (
        <div className="results">
          <h3>Analysis Results</h3>
          <p><strong>Position:</strong> {result.position}</p>
          <p><strong>Style:</strong> {result.style}</p>
          <p><strong>Color:</strong> {result.color}</p>
          <img src={result.image_url} alt="Analyzed outfit" />
        </div>
      )}

      {message && (
        <p className={`message ${message.includes('successful') ? 'success' : 'error'}`}>
          {message}
        </p>
      )}
    </div>
  );
}
