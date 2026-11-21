import { LiveDirections, LiveEvents, LiveSources, LiveAdd, Unsupported } from '../pages/LivePages';
import { CoveragePage } from '../pages/CoveragePage';
import { CompetitionPage, CompetitionsIndex, CompetitorsPage } from '../pages/CompetitionPages';
import { AccountPage } from '../pages/AccountPages';
import {
  AddWatch, Dashboard, Compare, CompetitionList, Competitors, ForecastForm, ForecastMethod,
  ForecastResult, ProfilePage, SettingsPage, StatusPage, Watchlist,
} from '../pages/AppPages';
import { Action, EmptyMessage } from '../shared/UI';
import { decodeRouteId } from './navigation';
import { NotFound } from './NotFound';

export function PrivateRoute({ path, tracked, onToggle }: {
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
    case '/app/profile': return new URLSearchParams(location.search).get('mode') === 'demo' ? <Unsupported><ProfilePage /></Unsupported> : <AccountPage />;
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
