import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:5000/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getAdminStats = () => api.get('/admin/stats');
export const getAdminAttendance = () => api.get('/admin/attendance');

export default api;
