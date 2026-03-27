import { useCallback } from 'react';

/**
 * Custom hook that provides a safe external redirect function.
 * Opens URLs in a new tab with `noopener noreferrer` for security.
 *
 * @returns {{ redirect: (url: string) => void }}
 */
export function useRedirect() {
  const redirect = useCallback((url) => {
    window.open(url, '_blank', 'noopener noreferrer');
  }, []);

  return { redirect };
}
