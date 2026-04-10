import React, { useState, useContext, useEffect } from 'react';
import styles from './StudentDashboard.module.css';
import { NavLink, useNavigate, Link } from 'react-router-dom';
import { AuthContext } from '../contexts/AuthContext';
import api from '../api';

export default function StudentDashboard() {
  const { user, logout } = useContext(AuthContext);
  const navigate = useNavigate();
  const [isBeneficiary, setIsBeneficiary] = useState(false);
  const [selectedPurpose, setSelectedPurpose] = useState('');
  const [file, setFile] = useState(null);
  
  const [scholarships, setScholarships] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Modal State
  const [applyingScholarship, setApplyingScholarship] = useState(null);
  const [requiredDocs, setRequiredDocs] = useState([]);
  const [selectedDocs, setSelectedDocs] = useState({});

  // Fund counter
  const [totalReceived, setTotalReceived] = useState(0);

  // Fetch real scholarships from backend
  useEffect(() => {
    const fetchScholarships = async () => {
      try {
        const response = await api.get('/scholarships');
        setScholarships(response.data);
      } catch (err) {
        console.error("Failed to fetch scholarships:", err);
        setError("Could not load scholarships. Please try again later.");
      } finally {
        setIsLoading(false);
      }
    };

    if (user) {
      fetchScholarships();
    }
  }, [user]);

  // Fetch total funds received from blockchain
  useEffect(() => {
    if (!user) return;
    const fetchFunds = async () => {
      try {
        const res = await api.get('/student/funds-received');
        setTotalReceived(res.data.total_received || 0);
      } catch (e) {
        console.warn('Could not fetch funds:', e);
      }
    };
    fetchFunds();
  }, [user]);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!selectedPurpose || !file) {
      alert("Select purpose and upload file.");
      return;
    }
    alert(`Success: Pending approval.`);
    setFile(null);
    setSelectedPurpose('');
  };

  const handleApplyClick = (scholar) => {
    // Context-aware document suggestions
    const docs = ["Student ID", "Admission Letter"];
    const text = (scholar.title + " " + scholar.description).toLowerCase();
    
    if (text.includes("engineer") || text.includes("stem") || text.includes("tech")) {
      docs.push("Entrance Rank Card");
    }
    if (text.includes("poor") || text.includes("income") || text.includes("underserved")) {
      docs.push("Income Certificate");
    }
    if (text.includes("academic") || text.includes("merit") || text.includes("scholar")) {
      docs.push("Previous Year Marksheet");
    }

    setRequiredDocs(docs);
    setApplyingScholarship(scholar);
    setSelectedDocs({});
  };

  const handleApplyFinal = async () => {
    if (!applyingScholarship) return;
    
    try {
      await api.post('/scholarships/apply', { 
        scheme_id: applyingScholarship.id,
        documents: selectedDocs 
      });
      alert("Application submitted successfully!");
      setApplyingScholarship(null);
    } catch (err) {
      console.error("Application error:", err);
      alert(err.response?.data?.detail || "Failed to submit application.");
    }
  };

  return (
    <div className={styles.container}>
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
        
        {user && (
          <button 
            className={styles.devToggle} 
            onClick={() => setIsBeneficiary(!isBeneficiary)}
          >
            [Demo] {isBeneficiary ? "Beneficiary" : "Applicant"}
          </button>
        )}
      </header>

      {user && (
        <div className={styles.fundBadgeRow}>
          💰 Total Fund Received: ₹{totalReceived.toLocaleString('en-IN')}
        </div>
      )}

      <main>
        {!user ? (
          <div className={styles.guestHero}>
            <h2 className={styles.sectionTitle}>Welcome to the Student Portal</h2>
            <p className={styles.guestText}>
              Sevafy provides a peer-to-peer grant system for students. 
              Please log in to browse available scholarships, track your applications, or request fund disbursements.
            </p>
            <Link to="/student-login" className={styles.actionBtn} style={{ display: 'inline-block', textAlign: 'center', textDecoration: 'none' }}>
              Log In to Get Started
            </Link>
          </div>
        ) : !isBeneficiary ? (
          <div className={styles.sectionBlock}>
            <h2 className={styles.sectionTitle}>Available Grants</h2>

            {isLoading ? (
              <div className={styles.telemetry}>Loading scholarships...</div>
            ) : error ? (
              <div className={styles.errorAlert}>{error}</div>
            ) : scholarships.length === 0 ? (
              <div className={styles.guestText}>No active scholarship schemes found.</div>
            ) : (
              <div className={styles.cardList}>
                {scholarships.map(scholar => (
                  <div key={scholar.id} className={styles.card}>
                    <div className={styles.cardHeader}>
                      <strong>{scholar.title}</strong>
                      {scholar.ngo_name && (
                        <div style={{ fontSize: '14px', color: '#666', fontWeight: 'bold', marginTop: '4px' }}>
                          By: {scholar.ngo_name}
                        </div>
                      )}
                    </div>
                    <div className={styles.cardBody}>
                      <div style={{ marginBottom: '8px' }}>{scholar.description}</div>
                      <div>Amount: ₹{parseFloat(scholar.amount_per_student).toLocaleString('en-IN')}</div>
                    </div>
                    <button 
                      className={styles.actionBtn}
                      onClick={() => handleApplyClick(scholar)}
                    >
                      Apply Now
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div className={styles.sectionBlock}>
            <h2 className={styles.sectionTitle}>Request Funds</h2>
            
            <form onSubmit={handleSubmit} className={styles.basicForm}>
              <div className={styles.formRow}>
                <label htmlFor="purposeSelect" className={styles.label}>1. Select Need:</label>
                <select 
                  id="purposeSelect" 
                  className={styles.hugeInput}
                  value={selectedPurpose}
                  onChange={(e) => setSelectedPurpose(e.target.value)}
                  required
                >
                  <option value="" disabled>-- TAP TO SELECT --</option>
                  <option value="Tuition">Tuition Fees</option>
                  <option value="Hostel">Hostel Fees</option>
                  <option value="Books">Books/Supplies</option>
                  <option value="Hardware">Laptop/Tablet</option>
                  <option value="Travel">Travel Allowed</option>
                  <option value="Medical">Medical Care</option>
                  <option value="Other">Other Expense</option>
                </select>
              </div>

              <div className={styles.formRow}>
                <label htmlFor="fileUpload" className={styles.label}>2. Upload Proof:</label>
                <input 
                  type="file" 
                  id="fileUpload" 
                  className={styles.fileControl}
                  onChange={handleFileChange}
                  accept=".pdf,image/*"
                  required
                />
              </div>

              <button type="submit" className={styles.submitBtn}>
                Submit Request
              </button>
            </form>
          </div>
        )}
      </main>

      <footer className={styles.footerData}>
        <hr className={styles.divider} />
        <div className={styles.telemetry}>
          Network: EDGE | Size: 12KB | Render: 4ms
        </div>
      </footer>

      {/* ── Application Modal ── */}
      {applyingScholarship && (
        <div className={styles.modalOverlay}>
          <div className={styles.modal}>
            <header className={styles.modalHeader}>
              <h3 className={styles.modalTitle}>Apply: {applyingScholarship.title}</h3>
            </header>
            <div className={styles.modalBody}>
              <p>To process your application for this <strong>{applyingScholarship.scheme_beneficiary}</strong> grant, please confirm you have the following documents ready:</p>
              
              <ul className={styles.checklist}>
                {requiredDocs.map(doc => (
                  <li key={doc} className={styles.checkItem}>
                    <input 
                      type="checkbox" 
                      id={doc} 
                      onChange={(e) => setSelectedDocs(prev => ({...prev, [doc]: e.target.checked ? "READY" : "MISSING"}))}
                    />
                    <label htmlFor={doc}>{doc}</label>
                  </li>
                ))}
              </ul>
              
              <p style={{fontSize: '14px', color: '#666'}}>* Digital copies will be required for AI verification in the next step.</p>
            </div>
            <footer className={styles.modalFooter}>
              <button 
                className={styles.secondaryBtn} 
                onClick={() => setApplyingScholarship(null)}
              >
                Cancel
              </button>
              <button 
                className={styles.actionBtn} 
                style={{flex: 2}}
                onClick={handleApplyFinal}
              >
                Submit Application
              </button>
            </footer>
          </div>
        </div>
      )}
    </div>
  );
}
