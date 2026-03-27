import React from 'react';
import { useScrollReveal } from '../hooks/useScrollReveal';
import styles from './MissionStrip.module.css';

/**
 * MissionStrip — full-width accent strip with the platform's one-liner and
 * a small body text explaining the blockchain-backed trust model.
 *
 * @returns {React.JSX.Element}
 */
export default function MissionStrip() {
  const ref = useScrollReveal();

  return (
    <section className={styles.strip} aria-label="Mission statement">
      <div className={`${styles.inner} reveal`} ref={ref}>
        <blockquote className={styles.quote}>
          "One donation. Multiple bonds. Zero bias."
        </blockquote>
        <p className={styles.body}>
          Our smart contracts hold funds and control the payment gateway API. The
          blockchain records every donor account, NGO account, amount, and
          timestamp — immutably.
        </p>
      </div>
    </section>
  );
}
