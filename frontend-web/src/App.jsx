import React, { useState, useEffect } from 'react';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Verificar si hay una sesión activa al cargar
    const token = localStorage.getItem('admin_token');
    if (token === 'admin-token-xyz') {
      setIsAuthenticated(true);
    }
    setLoading(false);
  }, []);

  const handleLoginSuccess = (token) => {
    localStorage.setItem('admin_token', token);
    setIsAuthenticated(true);
  };

  if (loading) return null; // O un splash screen corporativo

  return (
    <>
      {isAuthenticated ? (
        <Dashboard />
      ) : (
        <Login onLoginSuccess={handleLoginSuccess} />
      )}
    </>
  );
}

export default App;
