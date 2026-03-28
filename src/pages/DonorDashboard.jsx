import React, { useState, useEffect, useContext } from 'react';
import { AuthContext } from '../contexts/AuthContext';
import api from '../api';
import styles from './DonorDashboard.module.css';

const AMOUNTS = [100, 500, 1000, 5000];

// Hardcoded placeholder impact data (NOT from backend, as requested)
const PLACEHOLDER_IMPACT = [
  { ngo: 'Pratham Education Foundation', amount: 2500, date: '2025-12-15' },
  { ngo: 'Teach For India', amount: 1000, date: '2025-11-28' },
  { ngo: 'Akshaya Patra Foundation', amount: 5000, date: '2025-10-03' },
];

const PLACEHOLDER_STUDENTS = [
  { 
    id: 1, 
    name: 'Aarti K.', 
    school: 'Pratham Public School', 
    grade: '8th Grade', 
    amount: 1500, 
    message: '"Thank you! The new textbooks and uniform made my return to school wonderful."',
    image: 'https://picsum.photos/seed/stu1/100/100'
  },
  { 
    id: 2, 
    name: 'Rohan D.', 
    school: 'Vidya Gyan Academy', 
    grade: '10th Grade', 
    amount: 2000, 
    message: '"My scholarship covered the term fees that my family struggled with. I am preparing for my boards now!"',
    image: 'https://picsum.photos/seed/stu2/100/100'
  }
];

// Picsum placeholder images for NGO cards
const NGO_IMAGES = [
  'https://picsum.photos/seed/ngo1/600/300',
  'https://picsum.photos/seed/ngo2/600/300',
  'https://picsum.photos/seed/ngo3/600/300',
  'https://picsum.photos/seed/ngo4/600/300',
  'https://picsum.photos/seed/ngo5/600/300',
];

export default function DonorDashboard() {
  const { user } = useContext(AuthContext);
  const [ngos, setNgos] = useState([]);
  const [donorStatus, setDonorStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedAmounts, setSelectedAmounts] = useState({});
  const [customAmounts, setCustomAmounts] = useState({});
  const [donatingTo, setDonatingTo] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [ngosRes, statusRes] = await Promise.all([
          api.get('/ngos'),
          api.get('/donor/status'),
        ]);
        setNgos(ngosRes.data);
        setDonorStatus(statusRes.data);
      } catch (err) {
        console.error('Failed to fetch dashboard data:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleDonate = async (ngoId) => {
    const amount = selectedAmounts[ngoId] || Number(customAmounts[ngoId]);
    if (!amount || isNaN(amount) || amount <= 0) return;
    
    setDonatingTo(ngoId);
    try {
      const res = await api.post('/donate', { ngo_id: ngoId, amount });
      setDonorStatus({
        has_donated: true,
        total_donated: res.data.total_donated,
      });
      // Update NGO funding in local state
      setNgos(prev => prev.map(n => 
        n.id === ngoId 
          ? { ...n, net_funding: n.net_funding + amount }
          : n
      ));
    } catch (err) {
      console.error('Donation failed:', err);
    } finally {
      setDonatingTo(null);
    }
  };

  const selectAmount = (ngoId, amount) => {
    setSelectedAmounts(prev => ({
      ...prev,
      [ngoId]: prev[ngoId] === amount ? null : amount,
    }));
    setCustomAmounts(prev => ({ ...prev, [ngoId]: '' }));
  };

  const handleCustomAmountChange = (ngoId, value) => {
    setCustomAmounts(prev => ({ ...prev, [ngoId]: value }));
    setSelectedAmounts(prev => ({ ...prev, [ngoId]: null }));
  };

  if (loading) {
    return (
      <div className={styles.dashboardContainer}>
        <div className={styles.loading}>
          <span className={styles.spinner}></span>
          Loading your dashboard...
        </div>
      </div>
    );
  }

  const hasDonated = donorStatus?.has_donated;

  return (
    <div className={styles.dashboardContainer}>
      {/* ── Overlay: shown until first donation ──────── */}
      {!hasDonated && (
        <div className={styles.overlay}>
          <div className={styles.overlayIcon}>💝</div>
          <h2 className={styles.overlayTitle}>Make Your First Donation</h2>
          <p className={styles.overlaySubtitle}>
            Choose an NGO below and make your first contribution. Every rupee is tracked 
            transparently and goes directly towards education.
          </p>
        </div>
      )}

      {/* ── Post-Donation Dashboard ─────────────────── */}
      {hasDonated && (
        <>
          <div className={styles.welcomeBanner}>
            <div className={styles.welcomeText}>
              <h2>Welcome back, {user?.full_name?.split(' ')[0]} 👋</h2>
              <p>Your generosity is changing lives. Here's your impact so far.</p>
            </div>
            <div className={styles.totalDonated}>
              ₹{(donorStatus.total_donated || 0).toLocaleString('en-IN')}
            </div>
          </div>

          <h3 className={styles.sectionHeader}>Your Impact</h3>
          <div className={styles.impactGrid}>
            {PLACEHOLDER_IMPACT.map((item, idx) => (
              <div key={idx} className={styles.impactCard}>
                <div className={styles.impactNgo}>{item.ngo}</div>
                <div className={styles.impactAmount}>
                  ₹{item.amount.toLocaleString('en-IN')}
                </div>
                <div className={styles.impactDate}>
                  {new Date(item.date).toLocaleDateString('en-IN', {
                    year: 'numeric', month: 'long', day: 'numeric'
                  })}
                </div>
              </div>
            ))}
          </div>

          <h3 className={styles.sectionHeader}>Students Supported</h3>
          <div className={styles.studentGrid}>
            {PLACEHOLDER_STUDENTS.map((student) => (
              <div key={student.id} className={styles.studentCard}>
                <img src={student.image} alt={student.name} className={styles.studentAvatar} loading="lazy" />
                <div className={styles.studentInfo}>
                  <h4 className={styles.studentName}>{student.name}</h4>
                  <div className={styles.studentMeta}>
                    {student.grade} • {student.school}
                  </div>
                  <div className={styles.studentMessage}>
                    {student.message}
                  </div>
                </div>
                <div className={styles.studentAmount}>
                  ₹{student.amount.toLocaleString('en-IN')}
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* ── NGO Selection Grid (always visible) ─────── */}
      <h3 className={styles.sectionHeader}>
        {hasDonated ? 'Donate Again' : 'Choose an NGO to Support'}
      </h3>
      <div className={styles.ngoGrid}>
        {ngos.map((ngo, idx) => (
          <div key={ngo.id} className={styles.ngoCard}>
            <img
              src={NGO_IMAGES[idx % NGO_IMAGES.length]}
              alt={ngo.name}
              className={styles.ngoCardImage}
              loading="lazy"
            />
            <div className={styles.ngoCardBody}>
              <h4 className={styles.ngoCardName}>{ngo.name}</h4>
              <p className={styles.ngoCardAbout}>
                {ngo.about || ngo.description}
              </p>

              <div className={styles.beneficiaryTags}>
                {(ngo.beneficiary || []).map(tag => (
                  <span key={tag} className={styles.beneficiaryTag}>{tag}</span>
                ))}
              </div>

              <div className={styles.ngoCardMeta}>
                <span className={styles.ngoFunding}>
                  ₹{(ngo.net_funding || 0).toLocaleString('en-IN')} raised
                </span>
              </div>

              <div className={styles.amountPicker}>
                {AMOUNTS.map(amt => (
                  <button
                    key={amt}
                    className={`${styles.amountOption} ${
                      selectedAmounts[ngo.id] === amt ? styles.amountOptionActive : ''
                    }`}
                    onClick={() => selectAmount(ngo.id, amt)}
                  >
                    ₹{amt.toLocaleString('en-IN')}
                  </button>
                ))}
              </div>

              <input 
                type="number"
                min="1"
                placeholder="Custom Amount (₹)"
                className={styles.customAmountInput}
                value={customAmounts[ngo.id] || ''}
                onChange={(e) => handleCustomAmountChange(ngo.id, e.target.value)}
              />

              <button
                className={styles.donateBtn}
                disabled={(!selectedAmounts[ngo.id] && (!customAmounts[ngo.id] || customAmounts[ngo.id] <= 0)) || donatingTo === ngo.id}
                onClick={() => handleDonate(ngo.id)}
              >
                {donatingTo === ngo.id ? (
                  <><span className={styles.spinner}></span> Processing...</>
                ) : (selectedAmounts[ngo.id] || customAmounts[ngo.id]) ? (
                  `Donate ₹${Number(selectedAmounts[ngo.id] || customAmounts[ngo.id]).toLocaleString('en-IN')}`
                ) : (
                  'Select an amount'
                )}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
