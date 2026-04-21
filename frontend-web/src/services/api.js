import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:5000/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getAdminStats = () => api.get('/admin/stats');
export const getAdminAttendance = () => api.get('/admin/attendance');
export const getPendingExceptions = () => api.get('/admin/exceptions/pending');
export const resolveException = (logId, resolutionType, adminId = 'a1b2c3d4-0000-0000-0000-000000000002') => {
  return api.post('/admin/exceptions/resolve', { logId, resolutionType, adminId });
};

export default api;
