import { useEffect, useState } from 'react';
import { flushSync } from 'react-dom';

export function useManualReportPrint() {
  const [generatedAt, setGeneratedAt] = useState(() => new Date().toISOString());
  useEffect(() => {
    const beforePrint = () => {
      // Native print captures the DOM before another asynchronous React render.
      flushSync(() => setGeneratedAt(new Date().toISOString()));
    };
    window.addEventListener('beforeprint', beforePrint);
    return () => window.removeEventListener('beforeprint', beforePrint);
  }, []);
  function print() {
    setGeneratedAt(new Date().toISOString());
    requestAnimationFrame(() => window.print());
  }
  return { generatedAt, print };
}
