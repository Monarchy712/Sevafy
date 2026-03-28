import React, { useState, useContext } from 'react';
import styles from './StudentDashboard.module.css';
import { NavLink, useNavigate, Link } from 'react-router-dom';
import { AuthContext } from '../contexts/AuthContext';

export default function StudentDashboard() {
  const { user, logout } = useContext(AuthContext);
  const navigate = useNavigate();
  const [isBeneficiary, setIsBeneficiary] = useState(false);
  const [selectedPurpose, setSelectedPurpose] = useState('');
  const [file, setFile] = useState(null);

  const mockScholarships = [
    { id: 1, name: "Rural Merit 2026", amt: "Full Tuition", due: "15 Apr" },
    { id: 2, name: "STEM Village Grant", amt: "₹50,000", due: "1 May" },
    { id: 3, name: "Leader Award", amt: "₹25,000", due: "10 Jun" }
  ];

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
            
            <div className={styles.cardList}>
              {mockScholarships.map(scholar => (
                <div key={scholar.id} className={styles.card}>
                  <div className={styles.cardHeader}>
                    <strong>{scholar.name}</strong>
                  </div>
                  <div className={styles.cardBody}>
                    <div>Amount: {scholar.amt}</div>
                    <div className={styles.dueText}>Due: {scholar.due}</div>
                  </div>
                  <button className={styles.actionBtn}>Apply Now</button>
                </div>
              ))}
            </div>
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
    </div>
  );
}
