import React from 'react';
import { FEATURES } from '../constants';
import { useScrollReveal } from '../hooks/useScrollReveal';
import styles from './FeaturesGrid.module.css';

/**
 * Inline SVG icons keyed by feature ID.
 */
const FEATURE_ICONS = {
  'blockchain-ledger': (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <rect x="3" y="3" width="7" height="7" rx="1" stroke="currentColor" strokeWidth="1.5" />
      <rect x="14" y="3" width="7" height="7" rx="1" stroke="currentColor" strokeWidth="1.5" />
      <rect x="3" y="14" width="7" height="7" rx="1" stroke="currentColor" strokeWidth="1.5" />
      <rect x="14" y="14" width="7" height="7" rx="1" stroke="currentColor" strokeWidth="1.5" />
      <line x1="10" y1="6.5" x2="14" y2="6.5" stroke="currentColor" strokeWidth="1.5" />
      <line x1="10" y1="17.5" x2="14" y2="17.5" stroke="currentColor" strokeWidth="1.5" />
      <line x1="6.5" y1="10" x2="6.5" y2="14" stroke="currentColor" strokeWidth="1.5" />
      <line x1="17.5" y1="10" x2="17.5" y2="14" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  ),
  'ml-scholarship-finder': (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="10" cy="10" r="7" stroke="currentColor" strokeWidth="1.5" />
      <line x1="15" y1="15" x2="21" y2="21" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <path d="M7 10L10 13L14 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  'scam-ngo-detection': (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M12 2L3 7V12C3 17.5 7 21.5 12 22C17 21.5 21 17.5 21 12V7L12 2Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
      <line x1="12" y1="8" x2="12" y2="13" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <circle cx="12" cy="16" r="0.75" fill="currentColor" />
    </svg>
  ),
  'fund-flow-normalization': (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <polyline points="3,17 8,12 13,15 21,7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      <polyline points="16,7 21,7 21,12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  'transparent-disbursement': (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" strokeWidth="1.5" />
      <line x1="3" y1="9" x2="21" y2="9" stroke="currentColor" strokeWidth="1.5" />
      <line x1="9" y1="9" x2="9" y2="21" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  ),
  'donor-testimony-chain': (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M21 11.5C21 16.75 16.75 21 11.5 21L12.5 17" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <path d="M3 12.5C3 7.25 7.25 3 12.5 3L11.5 7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  ),
};

/**
 * FeatureTile — individual feature card wrapper for proper hook usage.
 *
 * @param {{ feature: object }} props
 * @returns {React.JSX.Element}
 */
function FeatureTile({ feature }) {
  const ref = useScrollReveal();

  return (
    <div ref={ref} className={`${styles.tile} reveal`}>
      <div className={styles.icon}>{FEATURE_ICONS[feature.id]}</div>
      <h3 className={styles.title}>{feature.title}</h3>
      <p className={styles.desc}>{feature.description}</p>
    </div>
  );
}

/**
 * FeaturesGrid — responsive grid of feature tiles.
 * Each tile contains an SVG icon, title, and one-line description.
 *
 * @returns {React.JSX.Element}
 */
export default function FeaturesGrid() {
  return (
    <section id="features" className={styles.section} aria-label="Platform features">
      <h2 className={styles.sectionTitle}>How It Works</h2>
      <div className={styles.grid}>
        {FEATURES.map((feature) => (
          <FeatureTile key={feature.id} feature={feature} />
        ))}
      </div>
    </section>
  );
}
