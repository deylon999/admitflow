import { LiveDirections, LiveEvents, LiveSources, LiveAdd, Unsupported } from './pages/LivePages';
import { CoveragePage } from './pages/CoveragePage';
import { CompetitionPage, CompetitionsIndex, CompetitorsPage } from './pages/CompetitionPages';
import { useEffect, useState } from 'react';
import { Header } from './components/Header';
import { Hero } from './components/Hero';
import { StatsStrip } from './components/StatsStrip';
import { Problems } from './components/Problems';
import { Features } from './components/Features';
import { Calculator } from './components/Calculator';
import { Competition } from './components/Competition';
import { Testimonial } from './components/Testimonial';
import { FAQ } from './components/FAQ';
import { FinalCTA } from './components/FinalCTA';
import { AppShell } from './app/Shell';
import { decodeRouteId, interceptInternalLinks } from './app/navigation';
import { Action, EmptyMessage } from './shared/UI';
import { AuthPage } from './pages/AuthPages';
import { ExamAnalytics, FaqPage, HowItWorks } from './pages/PublicPages';
import { AddWatch, Dashboard, Compare, CompetitionList, Competitors, ForecastForm, ForecastMethod, ForecastResult, ProfilePage, SettingsPage, StatusPage, Watchlist } from './pages/AppPages';
import { ProgramsCatalog, UniversityCatalog } from './catalog/CatalogPages';
import { ProgramDetail, UniversityPage } from './catalog/DetailPages';
import './catalog/catalog.css';
import './styles.css';
import './internal.css';

function usePathname(): string {
  const [path, setPath] = useState(() => (window.location.pathname.replace(/\/$/, '') || '/') + window.location.search);

  useEffect(() => {
    const onRouteChange = () => setPath((window.location.pathname.replace(/\/$/, '') || '/') + window.location.search);
    window.addEventListener('popstate', onRouteChange);
    document.addEventListener('click', interceptInternalLinks);
    return () => {
      window.removeEventListener('popstate', onRouteChange);
      document.removeEventListener('click', interceptInternalLinks);
    };
  }, []);

  return path;
}

function useTracked(): [string[], (id: string) => void] {
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

function LandingPage() {
  return (
    <div className="landing-page">
      <Header />
      <main>
        <Hero />
        <StatsStrip />
        <Problems />
        <Features />
        <Calculator />
        <Competition />
        <Testimonial />
        <FAQ />
        <FinalCTA />
      </main>

    </div>
  );
}

function PrivateRoute({ path, tracked, onToggle }: {
  path: string;
  tracked: string[];
  onToggle: (id: string) => void;
}) {
  if (/^\/app\/competitions\/[^/]+$/.test(path)) {
    const id = decodeRouteId(path.split('/').at(-1)!);
    if (!id) return <NotFound />;
    return id === 'mtuci-se' && new URLSearchParams(location.search).get('mode') === 'demo' ? <Unsupported><CompetitionList /></Unsupported> : <CompetitionPage key={path} id={id} />;
  }
  if (/^\/app\/watchlist\/[^/]+$/.test(path) && path !== '/app/watchlist/add') {
    const id = decodeRouteId(path.split('/').at(-1)!);
    return id ? <LiveDirections key={path} id={id} /> : <NotFound />;
  }
  // The design inventory keeps one illustrative competitors screen; real groups use the snapshot API.
  if (/^\/app\/competitions\/[^/]+\/competitors$/.test(path) && path !== '/app/competitions/mtuci-se/competitors') {
    const id = decodeRouteId(path.split('/').at(-2)!);
    return id ? <CompetitorsPage key={path} id={id} /> : <NotFound />;
  }
  switch (path) {
    case '/app': return new URLSearchParams(location.search).get('mode')==='demo' ? <Unsupported><Dashboard tracked={tracked}/></Unsupported> : <LiveDirections />;
    case '/app/competitions': return <CompetitionsIndex />;
    case '/app/profile': return <Unsupported><ProfilePage /></Unsupported>;
    case '/app/forecast': return <Unsupported><ForecastForm /></Unsupported>;
    case '/app/forecast/example': return <Unsupported><ForecastResult /></Unsupported>;
    case '/app/forecast/method': return <Unsupported><ForecastMethod /></Unsupported>;
    case '/app/watchlist': return new URLSearchParams(location.search).get('mode')==='demo' ? <Unsupported><Watchlist tracked={tracked} onToggle={onToggle} /></Unsupported> : <LiveDirections />;
    case '/app/watchlist/add': return new URLSearchParams(location.search).get('mode')==='demo' ? <Unsupported><AddWatch tracked={tracked} onToggle={onToggle} /></Unsupported> : <LiveAdd />;
    case '/app/competitions/mtuci-se/competitors': return <Unsupported><Competitors /></Unsupported>;
    case '/app/compare': return <Unsupported><Compare /></Unsupported>;
    case '/app/history': return <LiveEvents />;
    case '/app/notifications': return <LiveEvents />;
    case '/app/settings': return <Unsupported><SettingsPage /></Unsupported>;
    case '/app/sources': return <LiveSources />;
    case '/app/coverage': return <CoveragePage />;
    case '/app/states/empty': return <Unsupported><StatusPage variant="empty" /></Unsupported>;
    case '/app/states/error': return <Unsupported><StatusPage variant="error" /></Unsupported>;
    case '/app/states/success': return <Unsupported><StatusPage variant="success" /></Unsupported>;
    default: return <EmptyMessage title="Страница не найдена" description="Маршрут не предусмотрен прототипом." action={<Action to="/app">На главную ↗</Action>} />;
  }
}

function NotFound() {
  return <EmptyMessage title="Такой страницы нет" description="Проверь адрес или перейди к каталогу." action={<Action to="/universities">Каталог ↗</Action>} />;
}

function PublicRoute({ path }: { path: string }) {
  if (/^\/universities\/[^/]+$/.test(path)) {
    const id = decodeRouteId(path.slice('/universities/'.length));
    return id ? <UniversityPage key={path} id={id} /> : <NotFound />;
  }
  if (/^\/programs\/[^/]+$/.test(path)) {
    const id = decodeRouteId(path.slice('/programs/'.length));
    return id ? <ProgramDetail key={path} id={id} /> : <NotFound />;
  }
  switch (path) {
    case '/universities': return <UniversityCatalog />;
    case '/programs': return <ProgramsCatalog />;
    case '/ege-analytics': return <Unsupported><ExamAnalytics /></Unsupported>;
    case '/how-it-works': return <HowItWorks />;
    case '/faq': return <FaqPage />;
    default: return <NotFound />;
  }
}

export default function App() {
  const routeKey = usePathname();
  const pathname = routeKey.split('?')[0];
  const [tracked, onToggle] = useTracked();

  if (pathname === '/') return <LandingPage />;
  if (pathname === '/auth/login' || pathname === '/auth/register' || pathname === '/auth/recovery') {
    const mode = pathname === '/auth/register' ? 'register' : pathname === '/auth/recovery' ? 'recovery' : 'login';
    return <Unsupported key={pathname}><AuthPage mode={mode} /></Unsupported>;
  }
  const content = pathname === '/app' || pathname.startsWith('/app/')
    ? <PrivateRoute key={pathname} path={pathname} tracked={tracked} onToggle={onToggle} />
    : <PublicRoute path={pathname} />;
  // Catalog, university, program, EGE and private routes share one persistent sidebar.
  return <AppShell path={pathname}>{content}</AppShell>;
}
