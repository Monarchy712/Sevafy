import React, { createContext, useState, useEffect } from 'react';
import api from '../api';

export const AuthContext = createContext({
  user: null,
  login: async () => {},
  register: async () => {},
  logout: () => {},
  loading: true,
});

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Load user on startup if token exists
  useEffect(() => {
    const fetchUser = async () => {
      if (localStorage.getItem('token')) {
        try {
          const res = await api.get('/users/me');
          setUser(res.data);
        } catch (err) {
          console.error("Failed to load user info", err);
          localStorage.removeItem('token');
        }
      }
      setLoading(false);
    };
    fetchUser();
  }, []);

  const login = async (email, password) => {
    // Expected to be FormData per OAuth2 spec for access token endpoint
    const formData = new URLSearchParams();
    formData.append('username', email); // OAuth2 expects 'username' for email
    formData.append('password', password);

    const { data } = await api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    localStorage.setItem('token', data.access_token);
    
    // Fetch profile
    const profileRes = await api.get('/users/me');
    setUser(profileRes.data);
  };

  const register = async (userData) => {
    // userData has: email, password, full_name, role
    await api.post('/auth/register', userData);
    // Auto-login after registration is a good UX practice
    await login(userData.email, userData.password);
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
}
