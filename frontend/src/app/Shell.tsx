import type { ReactNode } from 'react';
import { RouteLink } from './RouteLink';

const navigation = [
  { to: '/app', icon: '▦', label: 'Обзор' },
  { to: '/app/forecast', icon: '◇', label: 'Мой прогноз' },
  { to: '/universities', icon: '▥', label: 'Вузы' },
  { to: '/programs', icon: '▤', label: 'Направления' },
  { to: '/app/watchlist', icon: '♡', label: 'Мои направления' },
  { to: '/app/competitions', icon: '☷', label: 'Конкурсные списки' },
  { to: '/app/compare', icon: '⇄', label: 'Сравнение' },
  { to: '/ege-analytics', icon: '▥', label: 'Аналитика ЕГЭ' },
  { to: '/app/history', icon: '◷', label: 'История' },
  { to: '/app/notifications', icon: '♧', label: 'Уведомления' },
  { to: '/app/settings', icon: '⚙', label: 'Настройки' },
];

function Brand() {
  return (
    <RouteLink className="af-brand" to="/">
      <span className="af-brand__mark">A</span>
      <strong>Абитуриент</strong>
    </RouteLink>
  );
}

export function AppHeader({ catalog = false }: { catalog?: boolean }) {
  return (
    <header className="af-app-header">
      <Brand />
      <div className="af-app-header__links">
        <RouteLink to="/universities">Вузы</RouteLink>
        <RouteLink to="/ege-analytics">ЕГЭ и проходные</RouteLink>
        <RouteLink to="/how-it-works">Как это работает</RouteLink>
      </div>
      <div className="af-app-header__right">
        <span className="af-campaign">{catalog ? 'КАТАЛОГ' : 'КАМПАНИЯ 2027'}</span>
        <RouteLink to="/app/notifications" aria-label="Уведомления" className="af-header-icon">♧</RouteLink>
        <RouteLink to="/app/profile" className="af-avatar">А</RouteLink>
      </div>
    </header>
  );
}

export function AppShell({ path, children }: { path: string; children: ReactNode }) {
  return (
    <div className="af-app">
      <AppHeader catalog={path.startsWith('/universities') || path.startsWith('/programs')} />
      <div className="af-app-layout">
        <aside className="af-sidebar" aria-label="Меню приложения">
          <div className="af-sidebar__caption">НАВИГАЦИЯ</div>
          <nav className="af-sidebar__nav">
            {navigation.map(item => (
              <RouteLink
                to={item.to}
                className={`af-sidebar__link ${path === item.to || (item.to !== '/app' && path.startsWith(item.to + '/')) ? 'is-active' : ''}`}
                key={item.to}
              >
                <span aria-hidden="true">{item.icon}</span>
                {item.label}
              </RouteLink>
            ))}
          </nav>
          <div className="af-sidebar__help">
            <b>Не уверен в выборе?</b>
            <p>Сравни направления и посмотри, что влияет на прогноз.</p>
            <RouteLink to="/app/compare">Сравнить варианты ↗</RouteLink>
          </div>
        </aside>
        <main className="af-main">
          <div className="af-main__inner">{children}</div>

        </main>
      </div>
      <nav className="af-mobile-nav" aria-label="Мобильная навигация">
        {navigation.slice(0, 5).map(item => (
          <RouteLink to={item.to} key={item.to} className={path === item.to ? 'is-active' : ''}>
            <span>{item.icon}</span>
            <small>{item.label.split(' ')[0]}</small>
          </RouteLink>
        ))}
      </nav>
    </div>
  );
}

