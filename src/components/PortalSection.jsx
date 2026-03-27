import React from 'react';
import { PORTALS } from '../constants';
import { useRedirect } from '../hooks/useRedirect';
import { useScrollReveal } from '../hooks/useScrollReveal';
import styles from './PortalSection.module.css';

/**
 * Inline SVG icon for the Student portal (graduation cap).
 * @returns {React.JSX.Element}
 */
function StudentIcon() {
  return (
    <svg width="32" height="32" viewBox="0 0 32 32" fill="none" aria-hidden="true">
      <path d="M16 4L2 12L16 20L30 12L16 4Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
      <path d="M8 16V24L16 28L24 24V16" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      <line x1="30" y1="12" x2="30" y2="22" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

/**
 * Inline SVG icon for the NGO portal (network nodes).
 * @returns {React.JSX.Element}
 */
function NgoIcon() {
  return (
    <svg width="32" height="32" viewBox="0 0 32 32" fill="none" aria-hidden="true">
      <circle cx="16" cy="8" r="3" stroke="currentColor" strokeWidth="1.5" />
      <circle cx="6" cy="24" r="3" stroke="currentColor" strokeWidth="1.5" />
      <circle cx="26" cy="24" r="3" stroke="currentColor" strokeWidth="1.5" />
      <line x1="16" y1="11" x2="6" y2="21" stroke="currentColor" strokeWidth="1.5" />
      <line x1="16" y1="11" x2="26" y2="21" stroke="currentColor" strokeWidth="1.5" />
      <line x1="9" y1="24" x2="23" y2="24" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  );
}

/**
 * Inline SVG icon for the Donor portal (heart + chain).
 * @returns {React.JSX.Element}
 */
function DonorIcon() {
  return (
    <svg width="32" height="32" viewBox="0 0 32 32" fill="none" aria-hidden="true">
      <path
        d="M16 28L4.5 17C2.5 15 2 12 3.5 9.5C5 7 8 6 10.5 7.5L16 12L21.5 7.5C24 6 27 7 28.5 9.5C30 12 29.5 15 27.5 17L16 28Z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
      <line x1="16" y1="18" x2="16" y2="24" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <circle cx="16" cy="26" r="1" fill="currentColor" />
    </svg>
  );
}

const ICONS = { student: StudentIcon, ngo: NgoIcon, donor: DonorIcon };

/**
 * PortalCard — individual portal card wrapper for proper hook usage.
 *
 * @param {{ portal: object, onRedirect: Function }} props
 * @returns {React.JSX.Element}
 */
function PortalCard({ portal, onRedirect }) {
  const ref = useScrollReveal();
  const Icon = ICONS[portal.id];

  return (
    <div
      ref={ref}
      className={`${styles.card} reveal`}
      role="button"
      tabIndex={0}
      aria-label={`${portal.heading} — ${portal.description}`}
      onClick={() => onRedirect(portal.url)}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onRedirect(portal.url);
        }
      }}
    >
      <div className={styles.icon}>
        <Icon />
      </div>
      <h3 className={styles.heading}>{portal.heading}</h3>
      <p className={styles.description}>{portal.description}</p>
      <span className={styles.arrow} aria-hidden="true">→</span>
    </div>
  );
}

/**
 * PortalSection — three clickable portal cards (Student, NGO, Donor).
 * Each card redirects externally via the useRedirect hook.
 *
 * @returns {React.JSX.Element}
 */
export default function PortalSection() {
  const { redirect } = useRedirect();

  const handleHowItWorks = () => {
    const el = document.getElementById('features');
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <section id="portals" className={styles.section} aria-label="Choose your portal">
      <h2 className={styles.sectionTitle}>Choose Your Portal</h2>
      <div className={styles.grid}>
        {PORTALS.map((portal) => (
          <PortalCard key={portal.id} portal={portal} onRedirect={redirect} />
        ))}
      </div>
      <div className={styles.ctaWrap}>
        <button
          className={styles.cta}
          onClick={handleHowItWorks}
          aria-label="How it works — scroll to features"
        >
          How It Works
          <span className={styles.ctaArrow} aria-hidden="true">↓</span>
        </button>
      </div>
    </section>
  );
}
