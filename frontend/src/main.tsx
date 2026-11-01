import React, { Suspense, lazy } from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClientProvider } from '@tanstack/react-query';
import { createQueryClient } from './lib/query-client';
import { BrowserRouter, Link, Route, Routes, useLocation } from 'react-router';
import { useEffect } from 'react';
import { Header, Footer } from './components/Layout';
import LandingPage from './pages/LandingPage';
import { api, sessionChangeKey } from './lib/api';
import { sessionAccessKey } from './lib/query-client';
import './styles.css';
import './tracker.css';

const TrackerPage = lazy(() => import('./pages/TrackerPage'));
const queryClient = createQueryClient();
function PagePosition() {
  const { pathname, hash } = useLocation();
  useEffect(() => {
    document.title = pathname === '/tracker' ? 'Мои направления — Абитуриент' : 'Абитуриент — ручные сценарии поступления';
    if (hash) requestAnimationFrame(() => document.getElementById(hash.slice(1))?.scrollIntoView());
    else window.scrollTo(0, 0);
  }, [pathname, hash]);
  return null;
}
function App() {
  useEffect(() => {
    const onStorage = (event: StorageEvent) => {
      if (event.key !== sessionChangeKey) return;
      api.forgetSession();
      queryClient.setQueryData(sessionAccessKey, 'changed');
      for (const key of ['watches', 'history', 'session-info']) void queryClient.cancelQueries({ queryKey: [key] });
    };
    window.addEventListener('storage', onStorage);
    return () => window.removeEventListener('storage', onStorage);
  }, []);
  return <><PagePosition /><Header /><Suspense fallback={<main className="container tracker-page"><p role="status">Загружаем страницу…</p></main>}><Routes><Route path="/" element={<LandingPage />} /><Route path="/tracker" element={<TrackerPage />} /><Route path="*" element={<main className="container tracker-page"><h1>Страница не найдена</h1><Link className="button button-primary" to="/">На главную</Link></main>} /></Routes></Suspense><Footer /></>;
}
ReactDOM.createRoot(document.getElementById('root')!).render(<React.StrictMode><QueryClientProvider client={queryClient}><BrowserRouter><App /></BrowserRouter></QueryClientProvider></React.StrictMode>);
