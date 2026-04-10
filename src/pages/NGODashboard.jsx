import React, { useContext, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts/AuthContext';
import api from '../api';
import ProgressTracker from '../components/ProgressTracker';
import styles from './NGODashboard.module.css';

// ── Impact Rating Display Helper ──────────────────────────────────
const TIER_CONFIG = {
  Platinum: { color: '#7C3AED', bg: 'rgba(124,58,237,0.1)', icon: '💎' },
  Gold:     { color: '#D97706', bg: 'rgba(217,119,6,0.12)', icon: '🏆' },
  Silver:   { color: '#6B7280', bg: 'rgba(107,114,128,0.1)', icon: '🥈' },
  Bronze:   { color: '#92400E', bg: 'rgba(146,64,14,0.12)', icon: '🥉' },
  Emerging: { color: '#2F855A', bg: 'rgba(47,133,90,0.1)',  icon: '🌱' },
};

// ── Utility: format currency ──────────────────────────────────────
const fmt = (n) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(n);
const fmtDate = (iso) => new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });

// ── Status Badge ──────────────────────────────────────────────────
function StatusBadge({ status }) {
  const map = {
    APPROVED: { label: 'Approved', cls: styles.badgeApproved },
    SUBMITTED: { label: 'Submitted', cls: styles.badgeSubmitted },
    UNDER_REVIEW: { label: 'Under Review', cls: styles.badgeReview },
    REJECTED: { label: 'Rejected', cls: styles.badgeRejected },
    PROCESSING: { label: 'Processing...', cls: styles.badgeProcessing },
    DISBURSED: { label: 'Paid Out', cls: styles.badgeDisbursed },
  };
  const cfg = map[status] || { label: status, cls: styles.badgeSubmitted };
  return <span className={`${styles.badge} ${cfg.cls}`}>{cfg.label}</span>;
}

// ── Impact Rating Widget ──────────────────────────────────────────
function ImpactRating({ rating, label, utilization }) {
  const tier = TIER_CONFIG[label] || TIER_CONFIG.Emerging;
  const pct = Math.round((rating / 5) * 100);
  const circumference = 2 * Math.PI * 54;
  const strokeDashoffset = circumference - (pct / 100) * circumference;

  return (
    <div className={styles.ratingWidget} style={{ '--tier-color': tier.color, '--tier-bg': tier.bg }}>
      <div className={styles.ratingCircleWrap}>
        <svg viewBox="0 0 120 120" className={styles.ratingRing}>
          <circle cx="60" cy="60" r="54" fill="none" stroke="var(--color-border)" strokeWidth="8" />
          <circle
            cx="60" cy="60" r="54" fill="none"
            stroke={tier.color} strokeWidth="8"
            strokeLinecap="round" strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            transform="rotate(-90 60 60)"
            style={{ transition: 'stroke-dashoffset 1.2s cubic-bezier(0.16,1,0.3,1)' }}
          />
        </svg>
        <div className={styles.ratingCenter}>
          <span className={styles.ratingIcon}>{tier.icon}</span>
          <span className={styles.ratingScore}>{rating.toFixed(1)}</span>
          <span className={styles.ratingMax}>/5.0</span>
        </div>
      </div>
      <div className={styles.ratingInfo}>
        <div className={styles.ratingTier} style={{ color: tier.color, background: tier.bg }}>
          {tier.icon} {label} Tier
        </div>
        <p className={styles.ratingDesc}>AI-Calculated Impact Score</p>
        <div className={styles.utilizationBar}>
          <span className={styles.utilizationLabel}>Fund Utilization</span>
          <div className={styles.utilizationTrack}>
            <div
              className={styles.utilizationFill}
              style={{ width: `${Math.round(utilization * 100)}%`, background: tier.color }}
            />
          </div>
          <span className={styles.utilizationPct}>{Math.round(utilization * 100)}%</span>
        </div>
      </div>
    </div>
  );
}

// ── Main Dashboard Component ──────────────────────────────────────
export default function NGODashboard() {
  const { user, loading } = useContext(AuthContext);
  const navigate = useNavigate();

  const [stats, setStats] = useState(null);
  const [donations, setDonations] = useState([]);
  const [scholarships, setScholarships] = useState([]);
  const [selectedApp, setSelectedApp] = useState(null);
  const [loadingStats, setLoadingStats] = useState(true);
  const [activeTab, setActiveTab] = useState('donations');
  const [approving, setApproving] = useState(null);
  const [fetchError, setFetchError] = useState(null);

  const handleApprove = async (appId) => {
    setApproving(appId);
    try {
      await api.post(`/ngo/scholarships/${appId}/approve`);
      // Refresh data
      const [statsRes, donationsRes, scholRes] = await Promise.all([
        api.get('/ngo/stats'),
        api.get('/ngo/donations'),
        api.get('/ngo/scholarships'),
      ]);
      setStats(statsRes.data);
      setDonations(donationsRes.data);
      setScholarships(scholRes.data);
    } catch (err) {
      console.error("Approval failed", err);
      const detail = err.response?.data?.detail || "Failed to approve scholarship. Please try again.";
      alert(detail);
      // Still refresh data to show current state
      try {
        const [statsRes, donationsRes, scholRes] = await Promise.all([
          api.get('/ngo/stats'),
          api.get('/ngo/donations'),
          api.get('/ngo/scholarships'),
        ]);
        setStats(statsRes.data);
        setDonations(donationsRes.data);
        setScholarships(scholRes.data);
      } catch (refreshErr) {
        console.warn('Could not refresh data after approval request — data may be slightly stale.');
      }
    } finally {
      setApproving(null);
    }
  };

  // ── Auth Guard: only NGO_PERSONNEL ────────────────────────────
  useEffect(() => {
    if (!loading) {
      if (!user) {
        navigate('/login');
      } else if (user.role !== 'NGO_PERSONNEL') {
        navigate('/');
      }
    }
  }, [user, loading, navigate]);

  // ── Fetch data ─────────────────────────────────────────────────
  useEffect(() => {
    if (!user || user.role !== 'NGO_PERSONNEL') return;

    const load = async () => {
      setLoadingStats(true);
      try {
        const [statsRes, donationsRes, scholRes] = await Promise.all([
          api.get('/ngo/stats'),
          api.get('/ngo/donations'),
          api.get('/ngo/scholarships'),
        ]);
        setStats(statsRes.data);
        setDonations(donationsRes.data);
        setScholarships(scholRes.data);
      } catch (err) {
        console.error('Failed to load NGO dashboard data:', err);
        setFetchError(err.response?.data?.detail || 'Failed to load dashboard data. Please refresh.');
      } finally {
        setLoadingStats(false);
      }
    };
    load();
  }, [user]);

  // ── Loading skeleton ───────────────────────────────────────────
  if (loading || loadingStats) {
    return (
      <div className={styles.loadingScreen}>
        <div className={styles.loadingOrb} />
        <p>Loading NGO Dashboard…</p>
      </div>
    );
  }

  if (fetchError) {
    return (
      <div className={styles.loadingScreen}>
        <p style={{ color: '#D32F2F', fontWeight: 'bold', fontSize: '1.2rem' }}>⚠ {fetchError}</p>
        <button className={styles.backBtn} onClick={() => window.location.reload()}>
          Retry
        </button>
      </div>
    );
  }

  if (!stats) return null;


  const tier = TIER_CONFIG[stats.impact_label] || TIER_CONFIG.Emerging;

  return (
    <div className={styles.dashboard}>
      {/* ── Header ──────────────────────────────────────────────── */}
      <header className={styles.header}>
        <div className={styles.headerContent}>
          <div>
            <div className={styles.headerTag}>
              Welcome, {user?.full_name.split(' ')[0]} • NGO Management Portal
            </div>
            <h1 className={styles.headerTitle}>{stats.ngo_name}</h1>
            <p className={styles.headerSub}>
              Blockchain UID:&nbsp;
              <code className={styles.uid}>#{stats.blockchain_uid}</code>
            </p>
          </div>
          <ImpactRating
            rating={stats.impact_rating}
            label={stats.impact_label}
            utilization={stats.utilization_rate}
          />
        </div>
      </header>

      {/* ── KPI Strip ───────────────────────────────────────────── */}
      <section className={styles.kpiStrip}>
        {[
          { label: 'Total Funding Received', value: fmt(stats.net_funding), sub: 'Net inflows', icon: '💰' },
          { label: 'Amount Disbursed', value: fmt(stats.total_disbursed), sub: 'To students', icon: '📤' },
          { label: 'Scholarships Approved', value: stats.scholarships_count, sub: 'Active beneficiaries', icon: '🎓' },
          { label: 'Avg. Per Student', value: fmt(stats.amount_per_student_avg), sub: 'Per scholarship', icon: '👤' },
        ].map((k, i) => (
          <div key={i} className={styles.kpiCard} style={{ animationDelay: `${i * 0.08}s` }}>
            <span className={styles.kpiIcon}>{k.icon}</span>
            <span className={styles.kpiValue}>{k.value}</span>
            <span className={styles.kpiLabel}>{k.label}</span>
            <span className={styles.kpiSub}>{k.sub}</span>
          </div>
        ))}
      </section>

      {/* ── Tabs ────────────────────────────────────────────────── */}
      <div className={styles.tabs}>
        <button
          className={`${styles.tab} ${activeTab === 'donations' ? styles.tabActive : ''}`}
          onClick={() => setActiveTab('donations')}
        >
          💳 Incoming Donations
          <span className={styles.tabCount}>{donations.length}</span>
        </button>
        <button
          className={`${styles.tab} ${activeTab === 'scholarships' ? styles.tabActive : ''}`}
          onClick={() => { setActiveTab('scholarships'); setSelectedApp(null); }}
        >
          🎓 Scholarship Pipeline
          <span className={styles.tabCount}>{scholarships.length}</span>
        </button>
      </div>

      {/* ── Tab Content ─────────────────────────────────────────── */}
      <div className={styles.tabContent}>

        {/* DONATIONS TAB */}
        {activeTab === 'donations' && (
          <div className={styles.donationTable}>
            <div className={styles.tableHeaderDonation}>
              <span>Donation #</span>
              <span>Sender UID</span>
              <span>Receiver UID</span>
              <span>Amount</span>
              <span>Timestamp</span>
            </div>
            {donations.length === 0 && (
              <div className={styles.emptyState}>No on-chain donations found.</div>
            )}
            {donations.map((d, i) => (
              <div key={i} className={styles.tableRowDonation} style={{ animationDelay: `${i * 0.05}s` }}>
                <span className={styles.donationNoCell}>{d.donation_no}</span>
                <span className={styles.uidCell}>{d.sender_uid}</span>
                <span className={styles.uidCell}>{d.receiver_uid}</span>
                <span className={styles.amountCell}>{fmt(d.amount)}</span>
                <span className={styles.dateCell}>{d.timestamp}</span>
              </div>
            ))}
          </div>
        )}

        {/* SCHOLARSHIPS TAB */}
        {activeTab === 'scholarships' && !selectedApp && (
          <div className={styles.donationTable}>
            <div className={styles.tableHeaderScholarship}>
              <span>Donation #</span>
              <span>Sender UID</span>
              <span>Receiver UID</span>
              <span>Amount</span>
              <span>Timestamp</span>
              <span>Purpose</span>
            </div>
            {scholarships.length === 0 && (
              <div className={styles.emptyState}>No scholarship pipeline data.</div>
            )}
            {scholarships.map((s, i) => (
              <div 
                key={i} 
                className={`${styles.tableRowScholarship} ${s.application_id && s.status !== 'SUBMITTED' ? styles.clickableRow : ''}`} 
                style={{ animationDelay: `${i * 0.05}s` }}
                onClick={() => { if (s.application_id && s.status !== 'SUBMITTED') setSelectedApp(s); }}
              >
                <span className={styles.donationNoCell}>{s.donation_no}</span>
                <span className={styles.uidCell} title={s.sender_uid}>{s.sender_uid}</span>
                <span className={styles.uidCell} title={s.receiver_uid}>{s.receiver_uid}</span>
                <span className={styles.amountCell}>{fmt(s.amount)}</span>
                <span className={styles.dateCell}>{s.timestamp}</span>
                <span className={styles.purposeCell}>
                  {s.status === 'SUBMITTED' ? (
                    <div className={styles.approveAction}>
                      <button 
                        className={styles.inlineApproveBtn}
                        onClick={(e) => { e.stopPropagation(); handleApprove(s.application_id); }}
                        disabled={approving === s.application_id}
                      >
                        {approving === s.application_id ? 'Wait...' : 'Approve'}
                      </button>
                    </div>
                  ) : s.status === 'APPROVED' ? (
                    <div className={styles.processingAction}>
                      <span className={styles.pulseDot} />
                      Processing Payout...
                    </div>
                  ) : (
                    <div className={styles.disbursedAction}>
                      <div className={styles.disbursedMain}>
                        <span className={styles.checkIcon}>✔</span>
                        {s.purpose}
                      </div>
                      {s.application_id && <span className={styles.viewBadge}>Details →</span>}
                    </div>
                  )}
                </span>
              </div>
            ))}
          </div>
        )}

        {/* PROGRESS TRACKER DETAIL VIEW */}
        {activeTab === 'scholarships' && selectedApp && (
          <div className={styles.detailView}>
            <button className={styles.backBtn} onClick={() => setSelectedApp(null)}>
              ← Back to Pipeline
            </button>
            <ProgressTracker application={selectedApp} />
          </div>
        )}
      </div>
    </div>
  );
}
