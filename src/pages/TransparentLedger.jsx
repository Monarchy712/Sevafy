import React, { useState, useEffect, useRef } from 'react';
import styles from './TransparentLedger.module.css';
import api from '../api';

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
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);
  const reconnectRef = useRef(null);

  // Fetch initial data from blockchain via backend
  useEffect(() => {
    const fetchLedger = async () => {
      try {
        const res = await api.get('/blockchain/ledger');
        setTransactions(res.data.transactions || []);
      } catch (err) {
        console.error('Failed to load ledger:', err);
        setError('Failed to load ledger data');
      } finally {
        setLoading(false);
      }
    };
    fetchLedger();
  }, []);

  // WebSocket connection for real-time updates
  useEffect(() => {
    let alive = true;

    const connect = () => {
      if (!alive) return;

      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/ledger`;

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
              <th>Type</th>
              <th>Donation #</th>
              <th>Sender UID</th>
              <th>Receiver UID</th>
              <th>Amount</th>
              <th>Purpose</th>
              <th>Time</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((tx, idx) => (
              <tr key={idx} className={styles.txRow} data-type={tx.tx_type}>
                <td>
                  <span className={styles.typeBadge} data-type={tx.tx_type}>
                    {tx.tx_type === 'DONOR_TO_NGO' ? '💰 Donation' : '🎓 Transfer'}
                  </span>
                </td>
                <td className={styles.donationId}>#{tx.donation_id}</td>
                <td className={styles.uidCell}>{tx.sender_uid}</td>
                <td className={styles.uidCell}>{tx.receiver_uid}</td>
                <td className={styles.amount}>
                  ₹{(tx.amount || 0).toLocaleString('en-IN')}
                </td>
                <td className={styles.purpose}>
                  {tx.purpose === 100 ? '—' : (PURPOSE_MAP[tx.purpose] || `Phase ${tx.purpose}`)}
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
