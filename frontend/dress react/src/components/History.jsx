import React, { useEffect, useState } from 'react';

export default function History({ username }) {
  const [uploads, setUploads] = useState([]);
  const [groupedUploads, setGroupedUploads] = useState({});

  useEffect(() => {
    fetchHistory();
  }, [username]);

  // Group uploads by position
  const groupByPosition = (uploads) => {
    return uploads.reduce((groups, upload) => {
      const pos = upload.style || 'Unknown';
      if (!groups[pos]) {
        groups[pos] = [];
      }
      groups[pos].push(upload);
      return groups;
    }, {});
  };

  const fetchHistory = async () => {
    try {
      const res = await fetch(`http://localhost:5000/history/${username}`);
      const data = await res.json();
      setUploads(data);
      setGroupedUploads(groupByPosition(data));
    } catch {
      setUploads([]);
      setGroupedUploads({});
    }
  };

  const handleDelete = async (uploadId) => {
    const res = await fetch('http://localhost:5000/delete_upload', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ upload_id: uploadId }),
    });

    const result = await res.json();
    if (result.status === 'success') {
      const updatedUploads = uploads.filter(upload => upload.id !== uploadId);
      setUploads(updatedUploads);
      setGroupedUploads(groupByPosition(updatedUploads));
    } else {
      alert('Failed to delete image.');
    }
  };

  return (
    <div>
      <h2>Your Upload History</h2>
      {uploads.length === 0 ? (
        <p>No uploads yet.</p>
      ) : (
        Object.keys(groupedUploads).map((position) => (
          <div key={position}>
            <h3>{position.toUpperCase()}</h3>
            <ul style={{ display: 'flex', flexWrap: 'wrap', gap: '16px' }}>
              {groupedUploads[position].map((upload) => (
                <li key={upload.id} style={{ listStyle: 'none', textAlign: 'center' }}>
                  <img src={upload.image_url} alt="uploaded" width="150" />
                  <p><strong>Position:</strong> {upload.position}</p>
                  <p><small>{new Date(upload.uploaded_at).toLocaleString()}</small></p>
                  <button onClick={() => handleDelete(upload.id)} style={{ color: 'red' }}>
                    Delete
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ))
      )}
    </div>
  );
}
