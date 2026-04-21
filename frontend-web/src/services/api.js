import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:5000/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const adminLogin = (username, password) => api.post('/admin/login', { username, password });
export const getAdminStats = () => api.get('/admin/stats');
export const getAdminAttendance = () => api.get('/admin/attendance');
export const getPendingExceptions = () => api.get('/admin/exceptions/pending');
export const resolveException = (logId, resolutionType, adminId = 'a1b2c3d4-0000-0000-0000-000000000002') => {
  return api.post('/admin/exceptions/resolve', { logId, resolutionType, adminId });
};

export const downloadAttendanceReport = async () => {
  const response = await api.get('/admin/export/csv', { responseType: 'blob' });
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', 'reporte_asistencia.csv');
  document.body.appendChild(link);
  link.click();
  link.remove();
};

export const getEmployees = () => api.get('/admin/employees');
export const createEmployee = (data) => api.post('/admin/employees', data);
export const getBuildings = () => api.get('/admin/buildings');
export const createBuilding = (data) => api.post('/admin/buildings', data);
export const getRoles = () => api.get('/admin/roles');

export default api;
