import React from 'react';
import styles from './HeroSection.module.css';

/**
 * HeroSection — premium hero with natively CSS-staggered headline and SVG animations.
 * Provides the same butter-smooth 60fps anime-style easing without the Vite dependency crashes.
 */
export default function HeroSection() {
  
  const renderHeadline = () => {
    const text1 = "Give without knowing.";
    const text2 = "Trust without doubt.";
    let totalIndex = 0;
    
    return (
      <>
        {text1.split(' ').map((word, i) => {
          totalIndex++;
          return (
            <span key={`w1-${i}`} className={styles.word} style={{ animationDelay: `${100 + totalIndex * 80}ms` }}>
              {word}
            </span>
          );
        })}
        <br />
        {text2.split(' ').map((word, i) => {
          totalIndex++;
          return (
            <span key={`w2-${i}`} className={styles.word} style={{ animationDelay: `${100 + totalIndex * 80}ms` }}>
              {word}
            </span>
          );
        })}
      </>
    );
  };

  return (
    <section className={styles.hero} aria-label="Hero">
      {/* Grid Pulse handled exclusively in CSS */}
      <div className={styles.grid} aria-hidden="true" />
      
      {/* Decorative SVG accent with CSS stroke animations */}
      <svg className={styles.accentSvg} viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
        <path className={styles.drawPath} fill="none" stroke="var(--color-accent)" strokeWidth="1" strokeOpacity="0.4" d="M 10,100 Q 50,20 100,100 T 190,100" />
        <circle className={styles.drawCircle1} cx="100" cy="100" r="40" fill="none" stroke="var(--color-secondary)" strokeWidth="0.5" strokeOpacity="0.4" />
        <circle className={styles.drawCircle2} cx="100" cy="100" r="30" fill="none" stroke="var(--color-accent)" strokeWidth="0.5" strokeOpacity="0.4" />
      </svg>

      <div className={styles.content}>
        <h1 className={styles.heading}>
          {renderHeadline()}
        </h1>
        <p className={styles.subtext}>
          Direct, transparent donations to verified NGOs.<br />
          No hidden fees. No bias. Just impact.
        </p>
        <div className={styles.actions}>
          <button 
            className="btn btn-primary" 
            onClick={() => {
              const el = document.getElementById('portals');
              if (el) el.scrollIntoView({ behavior: 'smooth' });
            }}
          >
            Choose Your Portal
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M7 7l5 5 5-5M7 13l5 5 5-5" />
            </svg>
          </button>
        </div>
      </div>
    </section>
  );
}
