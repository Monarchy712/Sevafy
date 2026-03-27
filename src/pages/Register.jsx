import React, { useState, useContext } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { AuthContext } from '../contexts/AuthContext';
import styles from './Auth.module.css';

export default function Register() {
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    password: '',
    role: 'STUDENT',
  });
  const [error, setError] = useState(null);
  const { register } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      await register(formData);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed.');
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
              <option value="NGO_PERSONNEL">NGO Representative</option>
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
          <button type="submit" className={styles.submitBtn}>
            Register
          </button>
        </form>

        <p className={styles.footerText}>
          Already have an account? <Link to="/login">Log in here</Link>
        </p>
      </div>
    </div>
  );
}
