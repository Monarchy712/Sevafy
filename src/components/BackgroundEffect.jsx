import React, { useEffect, useState } from 'react';
import styles from './BackgroundEffect.module.css';

/**
 * BackgroundEffect — organic, warm ambient orbs + floating SVG shapes.
 * Now features continuous, autonomous movement combined with cursor attraction.
 */
export default function BackgroundEffect() {
  const [blobs, setBlobs] = useState({
    orb1: { x: 50, y: 50 },
    orb2: { x: 50, y: 50 },
    orb3: { x: 50, y: 50 },
  });

  useEffect(() => {
    let raf;
    let mouse = { x: 50, y: 50 };
    
    // Core positions for the 3 orbs
    const current = {
      orb1: { x: 50, y: 50 },
      orb2: { x: 50, y: 50 },
      orb3: { x: 50, y: 50 }
    };

    const handleMouseMove = (e) => {
      mouse.x = (e.clientX / window.innerWidth) * 100;
      mouse.y = (e.clientY / window.innerHeight) * 100;
    };

    const lerp = (start, end, amt) => (1 - amt) * start + amt * end;

    const animate = (time) => {
      // Time-based autonomous motion (sine/cosine waves)
      const t = time * 0.0005; // speed of autonomous drift

      // Orb 1: large lazy drift, gently attracted to mouse
      const target1X = mouse.x * 0.4 + 20 + Math.sin(t) * 15;
      const target1Y = mouse.y * 0.4 + 20 + Math.cos(t * 0.8) * 15;
      
      // Orb 2: faster drift, opposite phase
      const target2X = 80 - mouse.x * 0.3 + Math.cos(t * 1.2) * 20;
      const target2Y = 80 - mouse.y * 0.3 + Math.sin(t * 0.9) * 20;

      // Orb 3: deep background, slow sweeping motion
      const target3X = 50 + Math.sin(t * 0.5) * 30;
      const target3Y = 50 + Math.cos(t * 0.6) * 30;

      // Smooth interpolation for fluid organic feel
      current.orb1.x = lerp(current.orb1.x, target1X, 0.02);
      current.orb1.y = lerp(current.orb1.y, target1Y, 0.02);
      
      current.orb2.x = lerp(current.orb2.x, target2X, 0.015);
      current.orb2.y = lerp(current.orb2.y, target2Y, 0.015);
      
      current.orb3.x = lerp(current.orb3.x, target3X, 0.01);
      current.orb3.y = lerp(current.orb3.y, target3Y, 0.01);

      setBlobs({
        orb1: { ...current.orb1 },
        orb2: { ...current.orb2 },
        orb3: { ...current.orb3 }
      });

      raf = requestAnimationFrame(animate);
    };

    window.addEventListener('mousemove', handleMouseMove);
    raf = requestAnimationFrame(animate);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      cancelAnimationFrame(raf);
    };
  }, []);

  return (
    <div className={styles.container} aria-hidden="true">
      <div className={styles.meshGradient} />

      <div
        className={styles.orb1}
        style={{ left: `${blobs.orb1.x}%`, top: `${blobs.orb1.y}%` }}
      />
      <div
        className={styles.orb2}
        style={{ left: `${blobs.orb2.x}%`, top: `${blobs.orb2.y}%` }}
      />
      <div
        className={styles.orb3}
        style={{ left: `${blobs.orb3.x}%`, top: `${blobs.orb3.y}%` }}
      />

      {/* Floating geometric accents - subtle sage and terracotta outlines */}
      <svg className={`${styles.floatShape} ${styles.shape1}`} width="140" height="140" viewBox="0 0 140 140" fill="none">
        <circle cx="70" cy="70" r="60" stroke="#2F855A" strokeOpacity="0.08" strokeWidth="1.5" />
        <circle cx="70" cy="70" r="45" stroke="#2F855A" strokeOpacity="0.04" strokeWidth="1" />
      </svg>
      <svg className={`${styles.floatShape} ${styles.shape2}`} width="100" height="100" viewBox="0 0 100 100" fill="none">
        <rect x="15" y="15" width="70" height="70" rx="16" stroke="#8B9A84" strokeOpacity="0.1" strokeWidth="1.5" transform="rotate(15 50 50)" />
      </svg>
      <svg className={`${styles.floatShape} ${styles.shape3}`} width="80" height="80" viewBox="0 0 80 80" fill="none">
        <polygon points="40,10 70,65 10,65" stroke="#2A2421" strokeOpacity="0.04" strokeWidth="1.5" fill="none" />
      </svg>
    </div>
  );
}
