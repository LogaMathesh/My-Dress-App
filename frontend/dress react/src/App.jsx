import React, { useState, useEffect } from 'react'; 
import './App.css';
import Header from './components/Header';
import Footer from './components/Footer';
import Login from './components/Login';
import Signup from './components/Signup';
import History from './components/History';
import Upload from './components/Upload';
import Suggestions from './components/Suggestions';
import Home from './components/Home';

function App() {
  const [view, setView] = useState('home');
  const [user, setUser] = useState(null);

  // Load user from localStorage on app load
  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      setUser(storedUser);
      setView('dashboard');
    }
  }, []);

  // Save user to localStorage on login
  const handleLogin = (username) => {
    setUser(username);
    localStorage.setItem('user', username);
    setView('dashboard');
  };

  // Clear user from localStorage on logout
  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('user');
    setView('home');
  };

  return (
    <div className="app">
      <Header user={user} setView={setView} handleLogout={handleLogout} />
      
      <main>
        {/* Unauthenticated routes */}
        {view === 'home' && <Home />}
        {view === 'login' && !user && <Login onLogin={handleLogin} />}
        {view === 'signup' && !user && <Signup onSignup={handleLogin} />}
        
        {/* Authenticated routes */}
        {user && (
          <>
            {view === 'dashboard' && <Upload username={user} />}
            {view === 'history' && <History username={user} />}
            {view === 'suggestions' && <Suggestions username={user} />}
          </>
        )}
      </main>

      <Footer />
    </div>
  );
}

export default App;
