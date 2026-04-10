import React, { useState, useEffect, useContext, useRef } from 'react';
import { AuthContext } from '../contexts/AuthContext';
import api from '../api';
import styles from './DonorDashboard.module.css';

const AMOUNTS = [100, 500, 1000, 5000];

// Purpose mapping from smart contract
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

// Picsum placeholder images for NGO cards
const NGO_IMAGES = [
  'https://picsum.photos/seed/ngo1/600/300',
  'https://picsum.photos/seed/ngo2/600/300',
  'https://picsum.photos/seed/ngo3/600/300',
  'https://picsum.photos/seed/ngo4/600/300',
  'https://picsum.photos/seed/ngo5/600/300',
];

function formatTimestamp(ts) {
  if (!ts) return '—';
  // Contract returns unix timestamp (uint256)
  const date = typeof ts === 'number' ? new Date(ts * 1000) : new Date(ts);
  if (isNaN(date.getTime())) return '—';
  return date.toLocaleDateString('en-IN', {
    year: 'numeric', month: 'long', day: 'numeric',
  });
}

export default function DonorDashboard() {
  const { user } = useContext(AuthContext);
  const [ngos, setNgos] = useState([]);
  const [donorStatus, setDonorStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedAmounts, setSelectedAmounts] = useState({});
  const [customAmounts, setCustomAmounts] = useState({});
  const [donatingTo, setDonatingTo] = useState(null);

  // Blockchain data from getUIDPaymentData()
  // Each record: { purpose, donation_id, sender_uid, receiver_uid, amount, timestamp, tx_type }
  const [blockchainTransactions, setBlockchainTransactions] = useState([]);
  const [lastTxResult, setLastTxResult] = useState(null);

  // WebSocket for real-time updates
  const wsRef = useRef(null);
  
  // Ref for scrolling to transactions
  const transRef = useRef(null);
  const [showThankYou, setShowThankYou] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [trackingResult, setTrackingResult] = useState(null);
  const [trackingLoading, setTrackingLoading] = useState(false);

  const handleTrackDonation = async (donationId, totalAmount) => {
    setTrackingLoading(true);
    try {
      const res = await api.get(`/blockchain/donation/${donationId}/students`);
      setTrackingResult({
        id: donationId,
        totalAmount: totalAmount || 0,
        data: res.data || []
      });
    } catch (err) {
      console.error('Failed to track donation:', err);
    } finally {
      setTrackingLoading(false);
    }
  };

  const closeTracking = () => setTrackingResult(null);

  // ---------- Fetch blockchain transactions ----------
  const fetchBlockchainData = async () => {
    try {
      const txRes = await api.get('/blockchain/my-transactions');
      setBlockchainTransactions(txRes.data || []);
    } catch (e) {
      console.warn('Blockchain data unavailable:', e);
    }
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [ngosRes, statusRes] = await Promise.all([
          api.get('/ngos'),
          api.get('/donor/status'),
        ]);
        setNgos(ngosRes.data);
        setDonorStatus(statusRes.data);

        // Fetch blockchain transactions via getUIDPaymentData()
        await fetchBlockchainData();
      } catch (err) {
        console.error('Failed to fetch dashboard data:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  // WebSocket for real-time donor updates
  useEffect(() => {
    if (!user) return;
    let alive = true;

    const connect = () => {
      if (!alive) return;
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const ws = new WebSocket(`${protocol}//${window.location.host}/ws/donor/${user.id}`);
      wsRef.current = ws;

      ws.onmessage = (event) => {
        if (event.data === 'pong') return;
        try {
          const payload = JSON.parse(event.data);
          if (payload.type === 'new_transaction') {
            // Refetch from blockchain for accurate data
            fetchBlockchainData();
          }
        } catch (e) {
          console.error('WS parse error:', e);
        }
      };

      ws.onclose = () => {
        if (alive) setTimeout(connect, 3000);
      };
      ws.onerror = () => ws.close();
    };

    connect();
    return () => {
      alive = false;
      if (wsRef.current) wsRef.current.close();
    };
  }, [user]);

  const handleDonate = async (ngoId) => {
    const amount = selectedAmounts[ngoId] || Number(customAmounts[ngoId]);
    if (!amount || isNaN(amount) || amount <= 0) return;

    setDonatingTo(ngoId);
    setLastTxResult(null);
    setIsRecording(true);

    try {
      const res = await api.post('/donate', { ngo_id: ngoId, amount });
      setDonorStatus({
        has_donated: true,
        total_donated: res.data.total_donated,
      });
      setNgos(prev => prev.map(n =>
        n.id === ngoId
          ? { ...n, net_funding: n.net_funding + amount }
          : n
      ));

      // Show blockchain result
      setLastTxResult({
        donation_id: res.data.donation_id,
        tx_hash: res.data.tx_hash,
        confirmed: res.data.confirmed,
        amount,
      });

      // Show Thank You overlay + scroll to ledger
      setIsRecording(false);
      setShowThankYou(true);
      setTimeout(() => setShowThankYou(false), 3000);

      // Smooth scroll to transactions
      setTimeout(() => {
        transRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 500);

      // ── Reliability Fix ─────────────────────────
      // Wait 1.5s for the blockchain node to index the new transaction
      await new Promise(r => setTimeout(r, 1500));
      await fetchBlockchainData();

    } catch (err) {
      setIsRecording(false);
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
      {/* ── Dashboard Content ────────────────────── */}
      {!hasDonated && !isRecording && (
          <div className={styles.overlay}>
            <div className={styles.overlayIcon}>💝</div>
            <h2 className={styles.overlayTitle}>Make Your First Donation</h2>
            <p className={styles.overlaySubtitle}>
              Choose an NGO below and make your first contribution. Every rupee is tracked
              transparently on the blockchain.
            </p>
          </div>
        )}

        {/* ── Recording Overlay ─────────────────────── */}
        {isRecording && (
          <div className={styles.recordingOverlay}>
            <div className={styles.recordingContent}>
              <div className={styles.blockchainLoader}>
                <div className={styles.cube}></div>
                <div className={styles.cube}></div>
                <div className={styles.cube}></div>
                <div className={styles.cube}></div>
              </div>
              <h2 className={styles.recordingTitle}>Recording on Chain...</h2>
              <p className={styles.recordingSubtitle}>
                Securing your donation on the blockchain ledger. 
                This usually takes less than 7 seconds on the testnet.
              </p>
              <div className={styles.donationBarContainer}>
                <div className={styles.donationBarFill}></div>
              </div>
            </div>
          </div>
        )}

      {/* ── Post-Donation Dashboard ─────────────────── */}
      {hasDonated && (
        <>
          <div className={styles.welcomeBanner}>
            <div className={styles.welcomeText}>
              <h2>Welcome back, {user?.full_name?.split(' ')[0]} 👋</h2>
              <p>Your generosity is changing lives. Here's your blockchain-verified impact.</p>
              {user?.blockchain_uid && (
                <span className={styles.uidBadge}>
                  Blockchain UID: {user.blockchain_uid}
                </span>
              )}
            </div>
            <div className={styles.totalDonated}>
              ₹{(donorStatus.total_donated || 0).toLocaleString('en-IN')}
            </div>
          </div>

          {/* Last Transaction Result */}
          {lastTxResult && lastTxResult.tx_hash && (
            <div className={styles.txResultBanner}>
              <div className={styles.txResultIcon}>✅</div>
              <div className={styles.txResultInfo}>
                <strong>Donation Recorded on Blockchain!</strong>
                <div className={styles.txResultMeta}>
                  Donation #{lastTxResult.donation_id} •
                  ₹{lastTxResult.amount.toLocaleString('en-IN')} •
                  <span className={styles.txHash} title={lastTxResult.tx_hash}>
                    TX: {lastTxResult.tx_hash.slice(0, 10)}...{lastTxResult.tx_hash.slice(-8)}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* ── Thank You Overlay ───────────────────── */}
          {showThankYou && (
            <div className={styles.thankYouOverlay}>
              <div className={styles.thankYouContent}>
                <div className={styles.thankYouIcon}>❤️</div>
                <h2 className={styles.thankYouHeading}>Thank You for Donating!</h2>
                <p className={styles.thankYouText}>Your contribution has been successfully recorded on the blockchain.</p>
              </div>
            </div>
          )}

          {/* --- Impact Audit: Blockchain Transparency Modal --- */}
          {trackingResult && (
            <div className={styles.auditOverlay} onClick={closeTracking}>
              <div className={styles.auditCard} onClick={e => e.stopPropagation()}>
                <button className={styles.auditCloseBtn} onClick={closeTracking}>&times;</button>
                
                {/* ── Progress Hero Area ───────────────── */}
                <div className={styles.auditHero}>
                  <div className={styles.auditHeaderRow}>
                    <div className={styles.auditBadge}>Donation Audit #{trackingResult.id}</div>
                    <div className={styles.auditVerifiedBadge}>
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                        <path d="M20 6L9 17L4 12"/>
                      </svg>
                      Verified on Chain
                    </div>
                  </div>
                  
                  <h3 className={styles.auditTitle}>Impact Realization</h3>
                  
                  {(() => {
                    const totalD = trackingResult.data.reduce((acc, curr) => acc + (curr.amount || 0), 0);
                    const totalA = trackingResult.totalAmount;
                    const percent = totalA > 0 ? (totalD / totalA) * 100 : 0;
                    
                    // Priority: RED(0%), YELLOW(partial), GREEN(100%)
                    const statusClass = percent === 0 ? styles.statusRed : (percent < 100 ? styles.statusYellow : styles.statusGreen);
                    const statusLabel = percent === 0 ? 'Awaiting' : (percent < 100 ? 'In Progress' : 'Completed');
                    
                    return (
                      <div className={styles.progressSection}>
                        <div className={styles.progressData}>
                          <span className={styles.progressLabel}>Blockchain Verified Disbursement</span>
                          <span className={`${styles.progressPercent} ${statusClass}`}>{Math.round(percent)}%</span>
                        </div>
                        <div className={styles.impactBarContainer}>
                          <div 
                            className={styles.impactBarFill}
                            style={{ 
                              width: `${percent}%`,
                              backgroundColor: percent === 0 ? '#ef4444' : (percent < 100 ? '#f59e0b' : '#22c55e')
                            }}
                          ></div>
                        </div>
                        <div className={styles.progressMeta}>
                          <span className={styles.amountSummary}>
                            <strong>₹{totalD.toLocaleString('en-IN')}</strong> / ₹{totalA.toLocaleString('en-IN')} Traceable
                          </span>
                          <span className={`${styles.auditPill} ${statusClass}`}>
                            {statusLabel}
                          </span>
                        </div>
                      </div>
                    );
                  })()}
                </div>

                {/* ── Blockchain Disbursement Timeline ── */}
                <div className={styles.auditTimeline}>
                  <div className={styles.timelineLabel}>Blockchain Audit Trail</div>
                  
                  {trackingResult.data.length > 0 ? (
                    <div className={styles.timelineList}>
                      {trackingResult.data.map((b, i) => (
                        <div key={i} className={styles.timelineItem}>
                          <div className={styles.timelineMarker}>
                            <div className={styles.markerInner}></div>
                          </div>
                          <div className={styles.timelineContent}>
                            <div className={styles.tRow}>
                              <span className={styles.tStudent}>Beneficiary Student #{b.receiver_uid}</span>
                              <span className={styles.tAmount}>₹{(b.amount || 0).toLocaleString('en-IN')}</span>
                            </div>
                            <div className={styles.tPurpose}>{PURPOSE_MAP[b.purpose] || `Audit Ref. ${b.purpose}`}</div>
                            <div className={styles.tDate}>
                              {new Date(b.timestamp * 1000).toLocaleString('en-IN', {
                                day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit'
                              })}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className={styles.auditEmpty}>
                      <div className={styles.emptyVault}>
                        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                          <rect x="2" y="5" width="20" height="14" rx="2" strokeOpacity="0.3"/>
                          <path d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z" strokeOpacity="0.4"/>
                          <path d="M22 12h-4M2 12h4" strokeOpacity="0.3"/>
                        </svg>
                      </div>
                      <h4>Funds Secured in Vault</h4>
                      <p>Your contribution is immutably locked on the SEVAFY contract. Once the NGO allocates these funds to specific students, the audit trail will populate here.</p>
                    </div>
                  )}
                </div>

                <div className={styles.auditFooter}>
                  <div className={styles.guardianShield}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/>
                    </svg>
                    Immutability Guaranteed by Blockchain
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ── Blockchain Transaction History ─────────── */}
          <h3 className={styles.sectionHeader} ref={transRef}>Your Donations (Blockchain Verified)</h3>

          {blockchainTransactions.length > 0 ? (
            <div className={styles.tableWrapper}>
              <table className={styles.blockchainTable}>
                <thead>
                  <tr>
                    <th>Donation #</th>
                    <th>Sender UID</th>
                    <th>Receiver UID</th>
                    <th>Amount</th>
                    <th>Timestamp</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {[...blockchainTransactions]
                    .sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0))
                    .map((tx, idx) => (
                      <tr 
                        key={idx} 
                        className={`${styles.txRow} ${tx.amount > 4999 ? styles.highValueRow : ''}`}
                      >
                      <td>
                        <span className={styles.donationBadge}>#{tx.donation_id}</span>
                      </td>
                      <td className={styles.uidCell}>
                        <div className={styles.uidWithBadge}>
                          <span className={styles.entityName}>
                            {tx.sender_uid === user?.blockchain_uid ? 'You' : user?.full_name}
                          </span>
                          <span className={styles.smallUid}>({tx.sender_uid})</span>
                          {tx.sender_uid === user?.blockchain_uid && (
                            <span className={styles.youBadge}>You</span>
                          )}
                        </div>
                      </td>
                      <td className={styles.uidCell}>
                        <div className={styles.uidWithBadge}>
                          <span className={styles.entityName}>
                            {ngos.find(n => n.blockchain_uid === tx.receiver_uid)?.name || 'Partner NGO'}
                          </span>
                          <span className={styles.smallUid}>({tx.receiver_uid})</span>
                        </div>
                      </td>
                      <td className={styles.amountCell}>
                        {(tx.amount || 0).toLocaleString('en-IN')}
                      </td>
                      <td className={styles.timeCell}>
                        {formatTimestamp(tx.timestamp)}
                      </td>
                      <td>
                        <button 
                          className="btn btn-ghost btn-sm"
                          onClick={() => handleTrackDonation(tx.donation_id, tx.amount)}
                          disabled={trackingLoading}
                        >
                          {trackingLoading && trackingResult?.id === tx.donation_id ? '...' : (
                            <>
                              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                                <circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>
                              </svg>
                              Track
                            </>
                          )}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className={styles.emptyState}>
              Your donations will appear here once confirmed on the blockchain.
            </div>
          )}
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
              src={ngo.logo_url || `https://picsum.photos/400/250?random=${idx}`}
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
                  <><span className={styles.spinner}></span> Recording on Blockchain...</>
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
