import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
});

// Har request mein JWT token chipkao agar hai toh
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export default api;
