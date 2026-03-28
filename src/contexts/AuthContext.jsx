import React, { createContext, useState, useEffect } from 'react';
import api from '../api';

export const AuthContext = createContext({
  user: null,
  login: async () => {},
  register: async () => {},
  loginWithGoogle: async () => {},
  loginWithGoogleCustom: async () => {},
  completeGoogleProfile: async () => {},
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
    // Backend expects schemas.UserLogin JSON body
    const { data } = await api.post('/auth/login', {
      email,
      password,
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

  const loginWithGoogle = async (credential) => {
    const { data } = await api.post('/auth/google', { credential });
    
    if (data.require_role) {
      // Return the partial profile so the frontend can redirect to role selection
      return { require_role: true, profile: data };
    } else {
      localStorage.setItem('token', data.access_token);
      const profileRes = await api.get('/users/me');
      setUser(profileRes.data);
      return { require_role: false };
    }
  };

  const loginWithGoogleCustom = async (access_token) => {
    const { data } = await api.post('/auth/google/custom', { access_token });
    
    if (data.require_role) {
      return { require_role: true, profile: data };
    } else {
      localStorage.setItem('token', data.access_token);
      const profileRes = await api.get('/users/me');
      setUser(profileRes.data);
      return { require_role: false };
    }
  };

  const completeGoogleProfile = async (profileData) => {
    const { data } = await api.post('/auth/google/complete', profileData);
    localStorage.setItem('token', data.access_token);
    const profileRes = await api.get('/users/me');
    setUser(profileRes.data);
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ 
      user, login, register, loginWithGoogle, loginWithGoogleCustom, completeGoogleProfile, logout, loading 
    }}>
      {children}
    </AuthContext.Provider>
  );
}
