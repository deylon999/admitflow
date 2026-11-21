import { useEffect } from 'react';
import { PrivateRoute } from './app/PrivateRoute';
import { PublicRoute } from './app/PublicRoute';
import { AppShell } from './app/Shell';
import { usePathname } from './app/usePathname';
import { Unsupported } from './features/demo/Unsupported';
import { useTracked } from './features/demo/useTracked';
import { LandingPage } from './features/public/LandingPage';
import { AuthPage, EmailActionPage } from './pages/AccountPages';
import { DemoAuthPage } from './pages/AuthPages';
import { enableAccount } from './shared/account';
import './catalog/catalog.css';
import './styles.css';
import './internal.css';

export default function App() {
  const route = usePathname();
  const routeKey = route.path;
  const pathname = routeKey.split('?')[0];
  const [tracked, onToggle] = useTracked();
  const demo = new URLSearchParams(routeKey.split('?')[1]).get('mode') === 'demo';
  const accountRoute = pathname === '/app' || pathname.startsWith('/app/') || pathname.startsWith('/auth/');
  useEffect(() => { enableAccount(!demo && accountRoute); }, [demo, accountRoute]);

  if (pathname === '/') return <LandingPage />;
  if (pathname === '/auth/login' || pathname === '/auth/register' || pathname === '/auth/recovery') {
    const mode = pathname === '/auth/register' ? 'register' : pathname === '/auth/recovery' ? 'recovery' : 'login';
    return demo ? <Unsupported key={pathname}><DemoAuthPage mode={mode}/></Unsupported> : <AuthPage key={pathname} mode={mode}/>;
  }
  if (pathname === '/auth/verify' || pathname === '/auth/reset') return demo ? <Unsupported><p>Техническая ссылка доступна в рабочем режиме.</p></Unsupported> : <EmailActionPage key={`${pathname}:${route.version}`} reset={pathname === '/auth/reset'}/>;
  const content = pathname === '/app' || pathname.startsWith('/app/')
    ? <PrivateRoute key={pathname} path={pathname} tracked={tracked} onToggle={onToggle} />
    : <PublicRoute path={pathname} />;
  // Catalog, university, program, EGE and private routes share one persistent sidebar.
  return <AppShell path={pathname}>{content}</AppShell>;
}
