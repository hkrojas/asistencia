import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:5000/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para incluir JWT en todas las peticiones administrativas
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('admin_token');
  if (token && config.url.includes('/admin')) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

// Interceptor para manejar errores 401 (Token expirado o inválido)
api.interceptors.response.use((response) => {
  return response;
}, (error) => {
  if (error.response?.status === 401 && !error.config.url.includes('/login')) {
    localStorage.removeItem('admin_token');
    // Forzar recarga a login solo si no estamos ya allí
    if (!window.location.pathname.includes('/login')) {
      window.location.href = '/login';
    }
  }
  return Promise.reject(error);
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
export const getPairingCode = (buildingId) => api.post('/admin/devices/pairing-code', { building_id: buildingId });
export const getRoles = () => api.get('/admin/roles');

export const getEmployeeSchedule = (id) => api.get(`/admin/employees/${id}/schedule`);
export const updateEmployeeSchedule = (id, data) => api.post(`/admin/employees/${id}/schedule`, data);

export const processTimesheets = (data) => api.post('/admin/timesheets/process', data);
export const createLeave = (data) => api.post('/admin/leaves', data);

export default api;
