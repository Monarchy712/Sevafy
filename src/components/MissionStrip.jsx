import React from 'react';
import { useScrollReveal } from '../hooks/useScrollReveal';
import styles from './MissionStrip.module.css';

/**
 * MissionStrip — full-width accent strip with the platform's one-liner.
 */
export default function MissionStrip() {
  const ref = useScrollReveal();

  return (
    <section className={styles.strip} aria-label="Mission statement">
      <div className={`${styles.inner} reveal`} ref={ref}>
        <blockquote className={styles.quote}>
          "One donation. Multiple lives changed. Zero bias."
        </blockquote>
        <p className={styles.body}>
          Every rupee is tracked, every NGO is verified, and every transaction
          is transparent — from the moment you donate to the moment it reaches
          someone who needs it.
        </p>
      </div>
    </section>
  );
}
