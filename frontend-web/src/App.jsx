import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import Employees from './pages/Employees';
import Buildings from './pages/Buildings';
import WfmManager from './pages/WfmManager';
import Operations from './pages/Operations';
import Prepayroll from './pages/Prepayroll';
import Payroll from './pages/Payroll';
import Payments from './pages/Payments';
import SystemAdmin from './pages/SystemAdmin';
import AdminLayout from './components/AdminLayout';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(() => Boolean(localStorage.getItem('admin_token')));

  const handleLoginSuccess = (token) => {
    localStorage.setItem('admin_token', token);
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('admin_token');
    setIsAuthenticated(false);
  };

  return (
    <BrowserRouter>
      <Routes>
        {/* Rutas Públicas */}
        <Route 
          path="/login" 
          element={
            isAuthenticated ? <Navigate to="/" replace /> : <Login onLoginSuccess={handleLoginSuccess} />
          } 
        />

        {/* Rutas Protegidas (Dashboard) */}
        <Route 
          path="/" 
          element={
            isAuthenticated ? <AdminLayout onLogout={handleLogout} /> : <Navigate to="/login" replace />
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="employees" element={<Employees />} />
          <Route path="buildings" element={<Buildings />} />
          <Route path="wfm" element={<WfmManager />} />
          <Route path="operations" element={<Operations />} />
          <Route path="prepayroll" element={<Prepayroll />} />
          <Route path="payroll" element={<Payroll />} />
          <Route path="payments" element={<Payments />} />
          <Route path="admin" element={<SystemAdmin />} />
        </Route>

        {/* Catch all - Redirect to dashboard */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
