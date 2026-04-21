import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:5000/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getAdminStats = () => api.get('/admin/stats');
export const getAdminAttendance = () => api.get('/admin/attendance');
export const resolveException = (logId, resolutionType, adminId = 1) => {
  // Por ahora simulado, imprimimos en consola
  console.log(`[API] Resolviendo incidencia ${logId} como ${resolutionType} (Admin: ${adminId})`);
  return api.post('/admin/exceptions/resolve', { logId, resolutionType, adminId });
};

export default api;
