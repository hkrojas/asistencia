import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';

const AdminLayout = ({ onLogout }) => {
  return (
    <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: '#f4f7f9' }}>
      <Sidebar onLogout={onLogout} />
      <main style={{ flex: 1, marginLeft: '260px', padding: '0px' }}>
        <Outlet />
      </main>
    </div>
  );
};

export default AdminLayout;
