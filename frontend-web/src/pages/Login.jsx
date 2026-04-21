import React, { useState } from 'react';
import { User, Lock, LogIn, AlertCircle } from 'lucide-react';
import { adminLogin } from '../services/api';
import './Login.css';

const Login = ({ onLoginSuccess }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await adminLogin(username, password);
      if (response.data.success) {
        onLoginSuccess(response.data.token);
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error al conectar con el servidor');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-overlay"></div>
      <div className="login-card">
        <div className="login-header">
          <div className="login-logo">
             {/* Logo Placeholder - Can be replaced with <img> if available */}
             <div className="logo-symbol">H</div>
             <div className="logo-text">GRUPO<span>HERNÁNDEZ</span></div>
          </div>
          <h1>Panel de Gestión WFM</h1>
          <p>Bienvenido. Inicie sesión para continuar.</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="username">Usuario</label>
            <div className="input-with-icon">
              <User size={18} />
              <input
                type="text"
                id="username"
                placeholder="Introduzca su usuario"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoFocus
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="password">Contraseña</label>
            <div className="input-with-icon">
              <Lock size={18} />
              <input
                type="password"
                id="password"
                placeholder="Introduzca su contraseña"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
          </div>

          {error && (
            <div className="login-error">
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          <button type="submit" className="login-button" disabled={loading}>
            {loading ? (
              <span className="loader"></span>
            ) : (
              <>
                <LogIn size={18} />
                Ingresar al Sistema
              </>
            )}
          </button>
        </form>

        <div className="login-footer">
          &copy; 2026 Grupo Hernández - Recursos Humanos
        </div>
      </div>
    </div>
  );
};

export default Login;
