import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  BarChart3, 
  Users, 
  Building2, 
  LogOut,
  ShieldCheck
} from 'lucide-react';
import './Sidebar.css';

const Sidebar = ({ onLogout }) => {
  return (
    <div className="sidebar">
      <div className="sidebar-logo">
        <ShieldCheck size={32} color="#D4AF37" />
        <div className="logo-text">
          <span className="brand-name">HERNÁNDEZ</span>
          <span className="app-name">Asistencia</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        <NavLink 
          to="/" 
          className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          end
        >
          <BarChart3 size={20} />
          <span>Asistencia</span>
        </NavLink>

        <NavLink 
          to="/employees" 
          className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
        >
          <Users size={20} />
          <span>Empleados</span>
        </NavLink>

        <NavLink 
          to="/buildings" 
          className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
        >
          <Building2 size={20} />
          <span>Sedes</span>
        </NavLink>
      </nav>

      <div className="sidebar-footer">
        <button className="logout-btn" onClick={onLogout}>
          <LogOut size={20} />
          <span>Cerrar Sesión</span>
        </button>
      </div>
    </div>
  );
};

export default Sidebar;
