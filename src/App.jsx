import React, { useContext } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, NavLink, useNavigate, useLocation } from 'react-router-dom';
import HeroSection from './components/HeroSection';
import PortalSection from './components/PortalSection';
import MissionStrip from './components/MissionStrip';
import FeaturesGrid from './components/FeaturesGrid';
import Footer from './components/Footer';

import { AuthProvider, AuthContext } from './contexts/AuthContext';
import { GoogleOAuthProvider } from '@react-oauth/google';
import Login from './pages/Login';
import Register from './pages/Register';
import SelectRole from './pages/SelectRole';
import DonorDashboard from './pages/DonorDashboard';
import BackgroundEffect from './components/BackgroundEffect';
import Recommendations from './pages/Recommendations';
import TransparentLedger from './pages/TransparentLedger';
import StudentDashboard from './pages/StudentDashboard';
import StudentLogin from './pages/StudentLogin';
import StudentRegister from './pages/StudentRegister';

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || "165731890815-08kfmug9japuoeivel432un7rkg05n7f.apps.googleusercontent.com";

import './App.css';

/**
 * NavBar — floating glass navigation bar with SEVAFY brand and auth buttons.
 */
function NavBar() {
  const { user, logout } = useContext(AuthContext);
  const navigate = useNavigate();

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        {/* Left: Brand */}
        <Link to="/" className="navbar-brand">
          <svg width="28" height="28" viewBox="0 0 32 32" fill="none" aria-hidden="true">
            <circle cx="16" cy="16" r="14" stroke="var(--color-accent)" strokeWidth="2" />
            <path d="M10 18C10 14 13 11 16 11C19 11 22 14 22 18" stroke="var(--color-accent)" strokeWidth="2" strokeLinecap="round" />
            <circle cx="16" cy="20" r="2" fill="var(--color-accent)" />
          </svg>
          <span>SEVAFY</span>
        </Link>

        {/* Center: Main Navigation */}
        <div className="navbar-center">
          {user?.role !== 'STUDENT' && (
            <NavLink to="/recommendations" className={({ isActive }) => `navbar-link ${isActive ? 'active' : ''}`}>AI Match</NavLink>
          )}
          <NavLink 
            to={user?.role === 'STUDENT' ? '/student-dashboard' : '/dashboard'} 
            className={({ isActive }) => `navbar-link ${isActive ? 'active' : ''}`}
          >
            Dashboard
          </NavLink>
          <NavLink to="/ledger" className={({ isActive }) => `navbar-link ${isActive ? 'active' : ''}`}>Ledger</NavLink>
        </div>

        {/* Right: Auth/Greeting */}
        <div className="navbar-auth">
          {user ? (
            <>
              <span className="navbar-greeting">
                {user.full_name.split(' ')[0]}
              </span>
              <button className="btn btn-secondary" onClick={() => { logout(); navigate('/'); }}>
                Log Out
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="btn btn-ghost">Log In</Link>
              <Link to="/register" className="btn btn-primary">
                Get Started
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                  <path d="M6 3L11 8L6 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}

/**
 * LandingPage — the main marketing page.
 */
function LandingPage() {
  return (
    <>
      <main>
        <HeroSection />
        <PortalSection />
        <MissionStrip />
        <FeaturesGrid />
      </main>
      <Footer />
    </>
  );
}

/**
 * AppContent — handles conditional NavBar based on AuthContext.
 */
function AppContent() {
  const { user } = useContext(AuthContext);
  const location = useLocation();
  const isStudentPath = location.pathname.startsWith('/student-');

  return (
    <>
      <BackgroundEffect />
      {/* Hide global NavBar on student-specific routes */}
      {!isStudentPath && user?.role !== 'STUDENT' && <NavBar />}
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/student-login" element={<StudentLogin />} />
        <Route path="/student-register" element={<StudentRegister />} />
        <Route path="/select-role" element={<SelectRole />} />
        <Route path="/recommendations" element={<Recommendations />} />
        <Route path="/dashboard" element={<DonorDashboard />} />
        <Route path="/student-dashboard" element={<StudentDashboard />} />
        <Route path="/student-ledger" element={<TransparentLedger />} />
        <Route path="/ledger" element={<TransparentLedger />} />
      </Routes>
    </>
  );
}

/**
 * App — root component.
 */
export default function App() {
  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <AuthProvider>
        <Router>
          <AppContent />
        </Router>
      </AuthProvider>
    </GoogleOAuthProvider>
  );
}
