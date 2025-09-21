import React from 'react';
import './Header.css';

export default function Header({ user, setView, handleLogout }) {
  return (
    <header className="header">
      <h1 className="app-title" onClick={() => setView('home')} style={{ cursor: 'pointer' }}>
        My Dress App
      </h1>

      <div className="auth-buttons">
        {!user ? (
          <>
            <button className="btn btn-outline" onClick={() => setView('login')}>🔐 Login</button>
            <button className="btn btn-primary" onClick={() => setView('signup')}>📝 Signup</button>
          </>
        ) : (
          <>
            <button className="btn btn-gradient" onClick={() => setView('dashboard')}>📤 Upload</button>
            <button className="btn btn-gradient" onClick={() => setView('history')}>📋 History</button>
            <button className="btn btn-gradient" onClick={() => setView('favorites')}>❤️ Favorites</button>
            <button className="btn btn-gradient" onClick={() => setView('suggestions')}>💡 Suggestions</button>
            <button className="btn btn-gradient" onClick={() => setView('chatbot')}>💬 Chatbot</button>
            <button className="btn btn-danger" onClick={handleLogout}>🚪 Logout</button>
          </>
        )}
      </div>
    </header>
  );
}
