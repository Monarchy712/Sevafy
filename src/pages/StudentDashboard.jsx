import React, { useState, useContext, useEffect, useRef } from 'react';
import styles from './StudentDashboard.module.css';
import { NavLink, useNavigate, Link } from 'react-router-dom';
import { AuthContext } from '../contexts/AuthContext';
import api from '../api';
import { animate } from 'animejs';

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
  
  // AI Verification State
  const [verificationStep, setVerificationStep] = useState('upload'); // upload | verifying | results
  const [uploadedFiles, setUploadedFiles] = useState({});
  const [verificationResults, setVerificationResults] = useState(null);
  const [isVerifying, setIsVerifying] = useState(false);
  
  const scannerRef = useRef(null);
  const scanLineRef = useRef(null);

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
    const docs = ["Identity Proof", "Admission Proof", "Income Proof", "Cancelled Cheque/Passbook", "Photograph of Applicant"];
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
    setVerificationStep('upload');
    setUploadedFiles({});
    setVerificationResults(null);
  };

  const handleFileSelect = (docName, file) => {
    setUploadedFiles(prev => ({ ...prev, [docName]: file }));
  };

  const runAIScan = async () => {
    if (!applyingScholarship) return;
    
    setVerificationStep('verifying');
    setIsVerifying(true);

    // Animation: Scanner moving up and down (Anime.js v4)
    if (scanLineRef.current) {
      animate(scanLineRef.current, {
        translateY: [0, 370]
      }, {
        duration: 1500,
        alternate: true,
        iterations: Infinity,
        easing: 'inOutQuad'
      });
    }

    // Simulate AI Workload
    await new Promise(r => setTimeout(r, 4000));

    const results = {};
    let overallPass = true;

    requiredDocs.forEach(doc => {
      const file = uploadedFiles[doc];
      if (!file) {
        results[doc] = { approved: false, criteria: [false, false, false], status: 'MISSING' };
        overallPass = false;
        return;
      }

      // Strict Parity Check: Even = Pass All, Odd = Fail All
      const digits = file.name.match(/\d+/g);
      const num = digits ? parseInt(digits.join('')) : 0;
      const isEven = num % 2 === 0;

      // All three criteria (Gemini, Claude, ChatGPT) follow the parity rule
      const c1 = isEven;
      const c2 = isEven;
      const c3 = isEven;

      const approved = isEven;

      results[doc] = {
        approved,
        criteria: [c1, c2, c3],
        status: approved ? 'APPROVED' : 'FAKE'
      };

      if (!approved) overallPass = false;
    });

    setVerificationResults({ results, overallPass });
    setVerificationStep('results');
    setIsVerifying(false);
  };

  const handleApplyFinal = async () => {
    if (!verificationResults?.overallPass) {
      alert("Verification failed. Please check your documents.");
      return;
    }

    // Convert file objects to statuses for the backend JSON request
    const documentStatus = {};
    requiredDocs.forEach(doc => {
      documentStatus[doc] = verificationResults.results[doc]?.status || "VERIFIED";
    });
    
    try {
      await api.post('/scholarships/apply', { 
        scheme_id: applyingScholarship.id,
        documents: documentStatus 
      });
      alert("Scholarship Approved & Application Submitted!");
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
              {verificationStep === 'upload' && (
                <>
                  <p>Upload digital copies of required documents for AI-powered verification.</p>
                  <div className={styles.uploadList}>
                    {requiredDocs.map(doc => (
                      <div key={doc} className={styles.uploadItem}>
                        <div className={styles.docLabel}>
                          <span className={styles.docName}>{doc}</span>
                          <span className={styles.fileName}>
                            {uploadedFiles[doc] ? uploadedFiles[doc].name : "No file selected"}
                          </span>
                        </div>
                        <div className={styles.fileInputWrapper}>
                          <button className={styles.uploadIconBtn}>
                            {uploadedFiles[doc] ? "Change" : "Upload"}
                          </button>
                          <input 
                            type="file" 
                            onChange={(e) => handleFileSelect(doc, e.target.files[0])}
                            accept="image/*,.pdf"
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                  <p style={{fontSize: '14px', color: '#666'}}>* Verification takes ~5 seconds using our AI vision engine.</p>
                </>
              )}

              {verificationStep === 'results' && (
                <div className={styles.resultsList}>
                  <h4 style={{ marginBottom: '12px' }}>Verification Summary</h4>
                  {requiredDocs.map(doc => {
                    const res = verificationResults.results[doc];
                    return (
                      <div key={doc} className={styles.resultCard}>
                        <div className={styles.resultCardHeader}>
                          <strong>{doc}</strong>
                          <span className={`${styles.resultStatus} ${res?.approved ? styles.statusApproved : styles.statusFake}`}>
                            {res?.status || 'UNKNOWN'}
                          </span>
                        </div>
                        <div className={styles.criteriaRow}>
                          <span className={`${styles.criteriaBadge} ${res?.criteria[0] ? styles.pass : styles.fail}`}>
                            {res?.criteria[0] ? '✓' : '✗'} Gemini
                          </span>
                          <span className={`${styles.criteriaBadge} ${res?.criteria[1] ? styles.pass : styles.fail}`}>
                            {res?.criteria[1] ? '✓' : '✗'} Claude
                          </span>
                          <span className={`${styles.criteriaBadge} ${res?.criteria[2] ? styles.pass : styles.fail}`}>
                            {res?.criteria[2] ? '✓' : '✗'} ChatGPT
                          </span>
                        </div>
                      </div>
                    );
                  })}

                  {verificationResults.overallPass ? (
                    <div className={styles.summaryBox}>
                      <div className={styles.summaryTitle}>Verification Success</div>
                      <div className={styles.summaryText}>All documents meet the required 2/3 consensus threshold.</div>
                    </div>
                  ) : (
                    <div className={`${styles.summaryBox} ${styles.statusFake}`}>
                      <div className={styles.summaryTitle}>Verification Failed</div>
                      <div className={styles.summaryText}>One or more documents flagged as invalid or fake.</div>
                    </div>
                  )}
                </div>
              )}
            </div>

            <footer className={styles.modalFooter}>
              <button 
                className={styles.secondaryBtn} 
                onClick={() => setApplyingScholarship(null)}
              >
                Cancel
              </button>
              
              {verificationStep === 'upload' && (
                <button 
                  className={styles.actionBtn} 
                  style={{flex: 2}}
                  onClick={runAIScan}
                  disabled={Object.keys(uploadedFiles).length < requiredDocs.length}
                >
                  Start Verification
                </button>
              )}

              {verificationStep === 'results' && verificationResults.overallPass && (
                <button 
                  className={styles.actionBtn} 
                  style={{flex: 2}}
                  onClick={handleApplyFinal}
                >
                  Complete Application
                </button>
              )}

              {verificationStep === 'results' && !verificationResults.overallPass && (
                <button 
                  className={styles.actionBtn} 
                  style={{flex: 2, backgroundColor: '#666'}}
                  onClick={() => setVerificationStep('upload')}
                >
                  Re-upload Missing
                </button>
              )}
            </footer>
          </div>
        </div>
      )}

      {/* ── Verifier Loading Overlay ── */}
      {isVerifying && (
        <div className={styles.verifierOverlay}>
          <div className={styles.scannerBox} ref={scannerRef}>
            <div className={styles.scanLine} ref={scanLineRef}></div>
            <div className={styles.scanContent}>
              {[1, 2, 3, 4, 5, 6].map(i => (
                <div key={i} className={styles.scanItemPlaceholder}>
                   <div className={styles.scanItemPlaceholderInner}></div>
                </div>
              ))}
            </div>
          </div>
          <h2 className={styles.verifierTitle}>AI Vision Verifier</h2>
          <p className={styles.verifierSubtitle}>
            Parallel processing across Gemini, Claude, and ChatGPT consensus engines for ultimate verification.
          </p>
        </div>
      )}
    </div>
  );
}
