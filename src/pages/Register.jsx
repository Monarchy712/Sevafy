import React, { useState, useContext } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { AuthContext } from '../contexts/AuthContext';
import { useGoogleLogin } from '@react-oauth/google';
import styles from './Auth.module.css';

export default function Register() {
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    password: '',
    role: 'STUDENT',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const { register, loginWithGoogleCustom } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleCustomGoogleLogin = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      setIsLoading(true);
      setError(null);
      try {
        const result = await loginWithGoogleCustom(tokenResponse.access_token);
        if (result.require_role) {
          navigate('/select-role', { state: { profile: result.profile } });
        } else {
          if (result.user?.role === 'STUDENT') {
            navigate('/student-dashboard');
          } else {
            navigate('/dashboard');
          }
        }
      } catch (err) {
        setError("Google Login failed. Please try again.");
      } finally {
        setIsLoading(false);
      }
    },
    onError: () => setError("Google Sign-In was unsuccessful.")
  });

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    try {
      await register(formData);
      if (formData.role === 'STUDENT') {
        navigate('/student-dashboard');
      } else {
        navigate('/dashboard');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={styles.authContainer}>
      <div className={styles.authCard}>
        <h2>Create an Account</h2>
        <p className={styles.subtitle}>Join the Sevafy ecosystem</p>
        
        {error && <div className={styles.errorAlert}>{error}</div>}

        <form onSubmit={handleSubmit} className={styles.authForm}>
          <div className={styles.formGroup}>
            <label htmlFor="role">I am a...</label>
            <select name="role" id="role" value={formData.role} onChange={handleChange}>
              <option value="STUDENT">Student</option>
              <option value="DONATOR">Donator</option>
            </select>
          </div>
          <div className={styles.formGroup}>
            <label htmlFor="full_name">Full Name</label>
            <input 
              id="full_name" 
              name="full_name"
              type="text" 
              value={formData.full_name} 
              onChange={handleChange} 
              required 
            />
          </div>
          <div className={styles.formGroup}>
            <label htmlFor="email">Email</label>
            <input 
              id="email" 
              name="email"
              type="email" 
              value={formData.email} 
              onChange={handleChange} 
              required 
            />
          </div>
          <div className={styles.formGroup}>
            <label htmlFor="password">Password</label>
            <input 
              id="password" 
              name="password"
              type="password" 
              value={formData.password} 
              onChange={handleChange} 
              required 
              minLength="6"
            />
          </div>
          <button type="submit" className={styles.submitBtn} disabled={isLoading}>
            {isLoading ? (
              <span className={styles.loader}>
                <span className={styles.spinner}></span>
                Establishing Account...
              </span>
            ) : (
              'Register'
            )}
          </button>
        </form>

        <div className={styles.separator}>
          <span>or sign in with</span>
        </div>

        <div className={styles.googleButtonWrapper}>
          <button 
            type="button" 
            className={styles.googleButtonCustom} 
            onClick={() => handleCustomGoogleLogin()}
            disabled={isLoading}
          >
            <div className={styles.googleIcon}>
              <svg viewBox="0 0 24 24" width="18" height="18" xmlns="http://www.w3.org/2000/svg">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05"/>
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
              </svg>
            </div>
            <span>Continue with Google</span>
          </button>
        </div>

        <p className={styles.footerText}>
          Already have an account? <Link to="/login">Log in here</Link>
        </p>
      </div>
    </div>
  );
}
