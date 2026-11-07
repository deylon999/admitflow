import { Link, NavLink, useLocation } from 'react-router';
import { useRef, useState } from 'react';
import { Button } from '@/shared/ui';
import { ThemeToggle } from './ThemeToggle';

export function Header() {
  const { pathname, hash, search } = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuButton = useRef<HTMLButtonElement>(null);
  const landing = pathname === '/';
  return (
    <header
      className="header"
      onKeyDown={(event) => {
        if (event.key === 'Escape' && menuOpen) {
          event.preventDefault();
          setMenuOpen(false);
          menuButton.current?.focus();
        }
      }}
    >
      <div className="container header-inner">
        <Link
          data-router-link
          className="brand"
          to="/"
          aria-label="Абитуриент — в начало"
          onClick={() => setMenuOpen(false)}
          aria-current={landing && !hash ? 'page' : undefined}
        >
          <span
            className="brand-mark"
            aria-hidden="true"
          />
          Абитуриент
        </Link>
        <Button
          ref={menuButton}
          variant="secondary"
          className="navigation-toggle"
          type="button"
          aria-expanded={menuOpen}
          aria-controls="site-navigation"
          onClick={() => setMenuOpen(!menuOpen)}
        >
          Разделы сайта <span aria-hidden="true">{menuOpen ? '−' : '+'}</span>
        </Button>
        <nav
          id="site-navigation"
          className="navigation"
          aria-label="Разделы сайта"
          data-open={menuOpen}
          onClickCapture={(event) => {
            const link = event.target instanceof Element ? event.target.closest('a') : null;
            if (!link) return;
            if (
              menuOpen &&
              link.pathname === pathname &&
              link.hash === hash &&
              link.search === search
            ) {
              event.preventDefault();
              requestAnimationFrame(() => menuButton.current?.focus());
            }
            setMenuOpen(false);
          }}
        >
          <Link
            data-router-link
            to="/#about"
            aria-current={landing && hash === '#about' ? 'location' : undefined}
          >
            О проекте
          </Link>
          <Link
            data-router-link
            to="/#calculator"
            aria-current={landing && hash === '#calculator' ? 'location' : undefined}
          >
            Калькулятор
          </Link>
          <NavLink
            data-router-link
            to="/sources"
            end
          >
            Источники
          </NavLink>
          <NavLink
            data-router-link
            to="/tracker"
            end
          >
            Мои направления
          </NavLink>
        </nav>
        <div className="header-actions">
          <ThemeToggle />
          <Link
            data-router-link
            className="button button-primary button-compact header-cta"
            to="/#calculator"
            onClick={() => setMenuOpen(false)}
          >
            <span className="desktop-label">Посчитать место</span>
            <span className="mobile-label">Посчитать</span>
          </Link>
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
