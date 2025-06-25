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
            <button onClick={() => setView('login')}>🔐 Login</button>
            <button onClick={() => setView('signup')}>📝 Signup</button>
          </>
        ) : (
          <>
            <button onClick={() => setView('dashboard')}>📤 Upload</button>
            <button onClick={() => setView('history')}>📋 History</button>
            <button onClick={() => setView('favorites')}>❤️ Favorites</button>
            <button onClick={() => setView('suggestions')}>💡 Suggestions</button>
            <button onClick={handleLogout}>🚪 Logout</button>
          </>
        )}
      </div>
    </header>
  );
}
