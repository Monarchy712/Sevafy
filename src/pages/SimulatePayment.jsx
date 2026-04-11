import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import api from '../api';
import styles from './SimulatePayment.module.css';

export default function SimulatePayment() {
  const { ngoId, amount, userId } = useParams();
  const [status, setStatus] = useState('processing'); // processing | success | error

  useEffect(() => {
    const triggerScan = async () => {
      try {
        // Simulate a slight delay for realistic "processing" feel
        await new Promise(r => setTimeout(r, 2000));
        
        await api.get(`/simulate-scan/${ngoId}/${amount}/${userId}`);
        setStatus('success');
      } catch (err) {
        console.error('Failed to simulate payment:', err);
        setStatus('error');
      }
    };

    if (ngoId && amount && userId) {
      triggerScan();
    }
  }, [ngoId, amount, userId]);

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        {status === 'processing' && (
          <>
            <div className={styles.spinner}></div>
            <h2 className={styles.title}>Processing Payment...</h2>
            <p className={styles.subtitle}>₹{parseFloat(amount).toLocaleString('en-IN')} to NGO</p>
            <div className={styles.progress}>
              <div className={styles.progressBar}></div>
            </div>
          </>
        )}

        {status === 'success' && (
          <>
            <div className={styles.successIcon}>✓</div>
            <h2 className={styles.title}>Payment Successful!</h2>
            <p className={styles.subtitle}>The dashboard on your desktop will update automatically.</p>
            <p className={styles.note}>You can close this tab now.</p>
          </>
        )}

        {status === 'error' && (
          <>
            <div className={styles.errorIcon}>!</div>
            <h2 className={styles.title}>Payment Failed</h2>
            <p className={styles.subtitle}>Could not connect to the SEVAFY server.</p>
            <button className={styles.retryBtn} onClick={() => window.location.reload()}>Retry</button>
          </>
        )}
      </div>
    </div>
  );
}
