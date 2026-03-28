import React, { useState, useContext, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts/AuthContext';
import styles from './Auth.module.css';

/**
 * SelectRole - Exclusive bridge for first-time Google users.
 * Ensures we capture the mandatory role selection before account finalization.
 */
export default function SelectRole() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const { completeGoogleProfile } = useContext(AuthContext);
  
  const [role, setRole] = useState('STUDENT');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Security redirect: can't access this page without a pending Google profile
  useEffect(() => {
    if (!state?.profile) {
      navigate('/login');
    }
  }, [state, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    
    try {
      await completeGoogleProfile({
        email: state.profile.email,
        full_name: state.profile.full_name,
        google_id: state.profile.google_id,
        role: role
      });
      navigate('/dashboard');
    } catch (err) {
      console.error("Profile completion error:", err);
      setError("Failed to finalize account. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  if (!state?.profile) return null;

  return (
    <div className={styles.authContainer}>
      <div className={styles.authCard}>
        <h2>One Last Step</h2>
        <p className={styles.subtitle}>Welcome aboard, {state.profile.full_name.split(' ')[0]}! How will you be using Sevafy?</p>
        
        {error && <div className={styles.errorAlert}>{error}</div>}

        <form onSubmit={handleSubmit} className={styles.authForm}>
          <div className={styles.formGroup}>
            <label htmlFor="role">Choose Your Portal</label>
            <select 
              id="role" 
              name="role"
              value={role} 
              onChange={(e) => setRole(e.target.value)}
              className={styles.roleSelect}
              required
            >
              <option value="STUDENT">Student (Seek Funding)</option>
              <option value="DONATOR">Donator (Sponsor Education)</option>
              <option value="NGO_PERSONNEL">NGO Representative (Manage Causes)</option>
            </select>
          </div>

          <button type="submit" className={styles.submitBtn} disabled={isLoading}>
            {isLoading ? (
              <span className={styles.loader}>
                <span className={styles.spinner}></span>
                Finalizing Portal...
              </span>
            ) : (
              'Complete Sign Up'
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
