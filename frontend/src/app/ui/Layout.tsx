import { Link, useLocation } from 'react-router';
import { ThemeToggle } from './ThemeToggle';

export function Header() {
  const pathname = useLocation().pathname;
  const tracker = pathname === '/tracker';
  const sources = pathname.startsWith('/sources');
  const secondary = pathname !== '/';
  return (
    <header className="header">
      <div className="container header-inner">
        <Link
          data-router-link
          className="brand"
          to="/"
          aria-label="Абитуриент — в начало"
        >
          <span
            className="brand-mark"
            aria-hidden="true"
          />
          Абитуриент
        </Link>
        <nav
          className="navigation"
          aria-label="Разделы сайта"
        >
          {sources ? (
            <span aria-current="page">Источники</span>
          ) : (
            <Link
              data-router-link
              to="/sources"
            >
              Источники
            </Link>
          )}
          {secondary ? (
            <>
              <Link
                data-router-link
                to="/"
              >
                О проекте
              </Link>
              <a href="/#calculator">Калькулятор</a>
              {tracker ? (
                <span aria-current="page">Мои направления</span>
              ) : (
                <Link
                  data-router-link
                  to="/tracker"
                >
                  Мои направления
                </Link>
              )}
            </>
          ) : (
            <>
              <a href="#problem">Проблема</a>
              <a href="#how-it-works">Почему номер не место</a>
              <a href="#calculator">Калькулятор</a>
              <a href="#questions">Вопросы</a>
            </>
          )}
        </nav>
        <div className="header-actions">
          <ThemeToggle />
          <a
            className="button button-primary header-cta"
            href={secondary ? '/#calculator' : '#calculator'}
          >
            <span className="desktop-label">Посчитать место</span>
            <span className="mobile-label">Посчитать</span>
          </a>
        </div>
      </div>
    </header>
  );
}
export function Footer() {
  return (
    <footer className="footer">
      <div className="container footer-inner">
        <span>
          Студенческий проект о поступлении. Материалы основаны на интервью с абитуриентами и
          репетиторами.
        </span>
        <Link
          data-router-link
          to="/tracker"
        >
          Мои направления →
        </Link>
      </div>
    </footer>
  );
}
