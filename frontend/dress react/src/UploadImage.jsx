import React, { useState, useEffect } from "react";
import axios from "axios";
import './App.css';

function UploadImage() {
  const username = "loga"; // Replace with dynamic user if needed
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [historyImages, setHistoryImages] = useState([]);

  useEffect(() => {
    fetchUploadHistory();
  }, []);

  const fetchUploadHistory = async () => {
    try {
      const response = await axios.get("http://localhost:5000/get_user_images", {
        params: { username }
      });
      if (response.data.image_data) {
        setHistoryImages(response.data.image_data);
      }
    } catch (err) {
      console.error("Error fetching history", err);
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setResults(null);
      setError(null);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      setError("Please select an image first");
      return;
    }

    const formData = new FormData();
    formData.append("image", selectedFile);
    formData.append("username", username);

    setIsLoading(true);
    setError(null);

    try {
      const response = await axios.post(
        "http://localhost:5000/upload_and_classify",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      if (response.data.success) {
        setResults({ top_prediction: response.data.top_prediction });
        fetchUploadHistory(); // Refresh image history
      } else {
        setError(response.data.error || "Classification failed");
      }
    } catch (err) {
      setError(err.response?.data?.error || "An error occurred");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container">
      <h1>Fashion Image Classifier</h1>
      <p>Upload an image to identify its category</p>

      <div className="upload-section">
        <input
          type="file"
          id="image-upload"
          accept="image/*"
          onChange={handleFileChange}
          className="file-input"
        />
        <label htmlFor="image-upload" className="upload-btn">
          Choose Image
        </label>
        {previewUrl && (
          <div className="image-preview">
            <img src={previewUrl} alt="Preview" />
          </div>
        )}
      </div>

      <button
        onClick={handleSubmit}
        disabled={!selectedFile || isLoading}
        className="submit-btn"
      >
        {isLoading ? "Classifying..." : "Classify Image"}
      </button>

      {error && <div className="error-message">{error}</div>}

      {results && results.top_prediction && (
        <div className="results-container">
          <h2>Classification Result</h2>
          <p>
            <strong>{results.top_prediction.label}</strong> (
            {(results.top_prediction.score * 100).toFixed(1)}% confidence)
          </p>
        </div>
      )}

      <div className="history-container">
        <h2>Upload History</h2>
        {historyImages.length === 0 ? (
          <p>No history available</p>
        ) : (
          <div className="history-grid">
            {historyImages.map((item, index) => (
              <div key={index} className="history-item">
                <img
                  src={`http://localhost:5000/${item.file_path.replace(/\\/g, "/")}`}
                  alt={`Upload ${index + 1}`}
                />
                <p>{item.classification.label} ({(item.classification.score * 100).toFixed(1)}%)</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default UploadImage;
