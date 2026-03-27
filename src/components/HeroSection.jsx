import React from 'react';
import styles from './HeroSection.module.css';

/**
 * HeroSection — header with tagline and subtitle.
 *
 * @returns {React.JSX.Element}
 */
export default function HeroSection() {
  return (
    <section className={styles.hero} aria-label="Hero">
      <div className={styles.grid} aria-hidden="true" />
      <div className={styles.content}>
        <h1 className={styles.heading}>
          Give without knowing.<br />Trust without doubt.
        </h1>
        <p className={styles.subtext}>
          Antigravity routes donations to verified NGOs through blockchain rails
          and ML vetting — disbursement is transparent, bias-free, and anonymous
          until confirmed.
        </p>
      </div>
    </section>
  );
}
