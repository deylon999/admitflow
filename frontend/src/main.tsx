import React, { Suspense, lazy } from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClientProvider } from '@tanstack/react-query';
import { createQueryClient } from './lib/query-client';
import { createBrowserRouter, Link, Outlet, RouterProvider, useLocation } from 'react-router';
import { useEffect } from 'react';
import { Header, Footer } from './components/Layout';
import LandingPage from './pages/LandingPage';
import { PageErrorBoundary } from './components/PageErrorBoundary';
import { api, sessionChangeKey } from './lib/api';
import { sessionAccessKey } from './lib/query-client';
import { clearDraft } from './lib/draft';
import './styles.css';
import './tracker.css';

const TrackerPage = lazy(() => import('./pages/TrackerPage'));
const SourcesPage = lazy(() => import('./pages/SourcesPage'));
const queryClient = createQueryClient();
function PagePosition() {
  const { pathname, hash } = useLocation();
  useEffect(() => {
    document.title = pathname.startsWith('/sources') ? 'Источники и группы — Абитуриент' : pathname === '/tracker' ? 'Мои направления — Абитуриент' : pathname === '/' ? 'Абитуриент — ручные сценарии поступления' : 'Страница не найдена — Абитуриент';
    const observer = new MutationObserver(position);
    function position() {
      const target = hash ? document.getElementById(hash.slice(1)) : document.querySelector<HTMLElement>('main h1');
      if (!target) return false;
      target.tabIndex = -1;
      target.focus({ preventScroll: true });
      if (hash) target.scrollIntoView(); else window.scrollTo(0, 0);
      observer.disconnect();
      return true;
    }
    if (!position()) observer.observe(document.getElementById('root')!, { childList: true, subtree: true });
    return () => observer.disconnect();
  }, [pathname, hash]);
  return null;
}
function App() {
  useEffect(() => {
    const onStorage = (event: StorageEvent) => {
      if (event.key !== sessionChangeKey) return;
      clearDraft();
      api.forgetSession();
      queryClient.setQueryData(sessionAccessKey, 'changed');
      for (const key of ['watches', 'history', 'session-info', 'archive-directions', 'direction-budget', 'archive-history', 'scenario', 'scenario-history', 'scenario-detail', 'changes']) void queryClient.cancelQueries({ queryKey: [key] });
    };
    window.addEventListener('storage', onStorage);
    return () => window.removeEventListener('storage', onStorage);
  }, []);
  return <><PagePosition /><a className="skip-link" href="#top" onClick={() => { const main = document.querySelector('main'); if (main) { main.tabIndex = -1; main.focus(); } }}>Перейти к содержимому</a><Header /><Suspense fallback={<main id="top" className="container tracker-page"><p role="status">Загружаем страницу…</p></main>}><Outlet /></Suspense><Footer /></>;
}
const router = createBrowserRouter([{ element: <PageErrorBoundary><App /></PageErrorBoundary>, children: [
  { index: true, element: <LandingPage /> },
  { path: 'tracker', element: <TrackerPage /> },
  { path: 'sources', element: <SourcesPage /> },
  { path: '*', element: <main id="top" className="container tracker-page"><h1>Страница не найдена</h1><Link className="button button-primary" to="/">На главную</Link></main> },
] }]);
ReactDOM.createRoot(document.getElementById('root')!).render(<React.StrictMode><QueryClientProvider client={queryClient}><RouterProvider router={router} /></QueryClientProvider></React.StrictMode>);
