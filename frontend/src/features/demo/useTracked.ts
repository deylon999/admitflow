import { useState } from 'react';

export function useTracked(): [string[], (id: string) => void] {
  const [tracked, setTracked] = useState<string[]>(() => {
    try {
      const data = window.localStorage.getItem('admitflow-demo-tracked');
      if (data) {
        const parsed = JSON.parse(data);
        if (Array.isArray(parsed)) return parsed.filter(x => typeof x === 'string');
      }
    } catch { /* demo works without storage */ }
    return ['mtuci-se', 'mirea-cs', 'mei-ai'];
  });

  function toggle(id: string) {
    setTracked(previous => {
      const next = previous.includes(id) ? previous.filter(x => x !== id) : [...previous, id];
      try { window.localStorage.setItem('admitflow-demo-tracked', JSON.stringify(next)); } catch { /* browser privacy mode */ }
      return next;
    });
  }

  return [tracked, toggle];
}
