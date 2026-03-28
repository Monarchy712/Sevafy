import React, { useState, useEffect, useRef, useContext } from 'react';
import { NavLink, useNavigate, Link } from 'react-router-dom';
import styles from './TransparentLedger.module.css';
import api from '../api';
import { AuthContext } from '../contexts/AuthContext';

// Purpose mapping from contract
const PURPOSE_MAP = {
  0: 'New Admission',
  1: 'Mid-Term Installment',
  2: 'Academic Renewal',
  3: 'Completion Status',
  4: 'Study Material Support',
  5: 'Hostel / Living Expense',
  6: 'Emergency Support',
  7: 'Dropout Recovery Support',
  8: 'Skill / Certification Support',
  9: 'Device / Tech Support',
  10: 'Performance Incentive',
  11: 'Special Category Support',
  100: 'Donation',
};

function formatTimestamp(ts) {
  if (!ts) return '—';
  // Contract returns unix timestamp (uint256 seconds)
  const date = typeof ts === 'number' ? new Date(ts * 1000) : new Date(ts);
  if (isNaN(date.getTime())) return '—';
  return date.toLocaleDateString('en-IN', {
    year: 'numeric', month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

export default function TransparentLedger() {
  const { user, logout } = useContext(AuthContext);
  const navigate = useNavigate();
  const isStudentPath = window.location.pathname === '/student-ledger';
  const isStudent = user?.role === 'STUDENT' || isStudentPath;
  const [transactions, setTransactions] = useState([]);
  const [ngos, setNgos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);
  const reconnectRef = useRef(null);

  // Fetch initial data from blockchain via backend
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [ledgerRes, ngosRes] = await Promise.all([
          api.get('/blockchain/ledger'),
          api.get('/ngos')
        ]);
        setTransactions(ledgerRes.data.transactions || []);
        setNgos(ngosRes.data || []);
      } catch (err) {
        console.error('Failed to load ledger data:', err);
        setError('Failed to load ledger data');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  // WebSocket connection for real-time updates
  useEffect(() => {
    let alive = true;

    const connect = () => {
      if (!alive) return;

      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      // Robust detection: if we're on Vite port (5173), target the backend port (8000)
      let host = window.location.host;
      if (host.includes('5173')) {
        host = host.replace('5173', '8000');
      }

      const wsUrl = `${protocol}//${host}/ws/ledger`;
      console.log('[Ledger] Connecting to WS:', wsUrl);

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        // Start heartbeat
        const heartbeat = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send('ping');
          } else {
            clearInterval(heartbeat);
          }
        }, 30000);
        ws._heartbeat = heartbeat;
      };

      ws.onmessage = (event) => {
        if (event.data === 'pong') return;

        try {
          const payload = JSON.parse(event.data);

          if (payload.type === 'new_transaction' || payload.type === 'blockchain_event') {
            setTransactions(prev => {
              // Check for duplicate donation_id and timestamp
              const exists = prev.some(t =>
                t.donation_id === payload.data.donation_id &&
                t.timestamp === payload.data.timestamp &&
                t.amount === payload.data.amount
              );
              if (exists) return prev;

              const updated = [payload.data, ...prev];
              // Keep max 50
              return updated.slice(0, 50);
            });
          }
        } catch (e) {
          console.error('WS parse error:', e);
        }
      };

      ws.onclose = () => {
        setConnected(false);
        clearInterval(ws._heartbeat);
        // Reconnect after delay
        if (alive) {
          reconnectRef.current = setTimeout(connect, 3000);
        }
      };

      ws.onerror = () => {
        ws.close();
      };
    };

    connect();

    return () => {
      alive = false;
      if (wsRef.current) wsRef.current.close();
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
    };
  }, []);

  if (loading) {
    return (
      <div className={styles.container}>
        <div className={styles.loading}>
          <span className={styles.spinner}></span>
          Loading Transparent Ledger...
        </div>
      </div>
    );
  }

  if (isStudent) {
    return (
      <div className={styles.containerBasic}>
        <header className={styles.simpleHeader}>
          <div className={styles.brandGroup}>
            <span className={styles.brandName}>SEVAFY</span>
            <nav className={styles.simpleNav}>
              <NavLink to="/student-dashboard" className={({ isActive }) => `${styles.navItem} ${isActive ? styles.active : ''}`}>Portal</NavLink>
              <NavLink to="/student-ledger" className={({ isActive }) => `${styles.navItem} ${isActive ? styles.active : ''}`}>Ledger</NavLink>
              {user ? (
                <button className={styles.navLinkBtn} onClick={() => { logout(); navigate('/student-dashboard'); }}>Log Out</button>
              ) : (
                <Link to="/student-login" className={styles.navItem}>Log In</Link>
              )}
            </nav>
          </div>
        </header>

        <div className={styles.headerBasic}>
          <h1 className={styles.titleBasic}>Transaction Ledger</h1>
          <p className={styles.subtitleBasic}>Historical record of verified transfers</p>
        </div>

        {error && <div className={styles.errorBanner}>{error}</div>}

        <div className={styles.tableWrapperBasic}>
          <table className={styles.tableBasic}>
            <thead>
              <tr>
                <th>ID</th>
                <th>Source</th>
                <th>Destination</th>
                <th>Amount</th>
                <th>Purpose</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((tx, idx) => (
                <tr key={idx}>
                  <td>#{tx.donation_id}</td>
                  <td>{tx.sender_uid}</td>
                  <td>
                    {ngos.find(n => n.blockchain_uid === tx.receiver_uid)?.name || tx.receiver_uid}
                  </td>
                  <td>₹{(tx.amount || 0).toLocaleString('en-IN')}</td>
                  <td>
                    {tx.purpose === 100 ? 'Donation' : (PURPOSE_MAP[tx.purpose] || `Phase ${tx.purpose}`)}
                  </td>
                  <td>{formatTimestamp(tx.timestamp)}</td>
                </tr>
              ))}
              {transactions.length === 0 && (
                <tr>
                  <td colSpan="6" style={{ textAlign: 'center', padding: '2rem' }}>No records found.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>
            <span className={styles.titleIcon}>📊</span>
            Transparent Ledger
          </h1>
          <p className={styles.subtitle}>
            Every transaction recorded immutably on the blockchain
          </p>
        </div>
        <div className={styles.statusBadge} data-connected={connected}>
          <span className={styles.statusDot}></span>
          {connected ? 'Live' : 'Connecting...'}
        </div>
      </div>

      {error && (
        <div className={styles.errorBanner}>{error}</div>
      )}

      <div className={styles.statsRow}>
        <div className={styles.statCard}>
          <div className={styles.statValue}>{transactions.length}</div>
          <div className={styles.statLabel}>Transactions</div>
        </div>
        <div className={styles.statCard}>
          <div className={styles.statValue}>
            {transactions.filter(t => t.tx_type === 'DONOR_TO_NGO').length}
          </div>
          <div className={styles.statLabel}>Donations</div>
        </div>
        <div className={styles.statCard}>
          <div className={styles.statValue}>
            {transactions.filter(t => t.tx_type === 'NGO_TO_STUDENT').length}
          </div>
          <div className={styles.statLabel}>Fund Transfers</div>
        </div>
        <div className={styles.statCard}>
          <div className={styles.statValue}>
            ₹{transactions.reduce((sum, t) => sum + (t.amount || 0), 0).toLocaleString('en-IN')}
          </div>
          <div className={styles.statLabel}>Total Volume</div>
        </div>
      </div>

      <div className={styles.tableWrapper}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Donation #</th>
              <th>Sender UID</th>
              <th>NGO</th>
              <th>Amount</th>
              <th>Purpose</th>
              <th>Time</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((tx, idx) => (
              <tr
                key={idx}
                className={`${styles.txRow} ${tx.amount > 4999 ? styles.highValueRow : ''}`}
                data-type={tx.tx_type}
              >
                <td className={styles.donationId}>#{tx.donation_id}</td>
                <td className={styles.uidCell}>{tx.sender_uid}</td>
                <td className={styles.uidCell}>
                  {ngos.find(n => n.blockchain_uid === tx.receiver_uid)?.name || tx.receiver_uid}
                </td>
                <td className={styles.amount}>
                  ₹{(tx.amount || 0).toLocaleString('en-IN')}
                </td>
                <td className={styles.purpose}>
                  {tx.purpose === 100 ? 'Donation' : (PURPOSE_MAP[tx.purpose] || `Phase ${tx.purpose}`)}
                </td>
                <td className={styles.time}>{formatTimestamp(tx.timestamp)}</td>
              </tr>
            ))}
            {transactions.length === 0 && (
              <tr>
                <td colSpan="7" className={styles.empty}>
                  No transactions yet. Make a donation to see it appear here in real-time!
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
