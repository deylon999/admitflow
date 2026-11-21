import { useEffect, useState } from 'react';
import { captureAuthLink } from '../shared/authLink';
import { interceptInternalLinks } from './navigation';

export function usePathname(): { path: string; version: number } {
  const [path, setPath] = useState(() => ({ path: (window.location.pathname.replace(/\/$/, '') || '/') + window.location.search, version: 0 }));

  useEffect(() => {
    const onRouteChange = () => {
      captureAuthLink();
      setPath(previous => ({ path: (window.location.pathname.replace(/\/$/, '') || '/') + window.location.search, version: previous.version + 1 }));
    };
    window.addEventListener('popstate', onRouteChange);
    document.addEventListener('click', interceptInternalLinks);
    return () => {
      window.removeEventListener('popstate', onRouteChange);
      document.removeEventListener('click', interceptInternalLinks);
    };
  }, []);

  return path;
}
