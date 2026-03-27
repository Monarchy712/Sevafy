import { useEffect, useRef } from 'react';

/**
 * Custom hook — animates elements when they enter the viewport via Intersection Observer.
 * Adds the `visible` class when the element is in view.
 *
 * @param {{ threshold?: number, rootMargin?: string }} options
 * @returns {React.RefObject}
 */
export function useScrollReveal(options = {}) {
  const ref = useRef(null);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      },
      { threshold: options.threshold ?? 0.15, rootMargin: options.rootMargin ?? '0px' }
    );

    observer.observe(node);
    return () => observer.disconnect();
  }, [options.threshold, options.rootMargin]);

  return ref;
}
