import { Link, useLocation } from 'react-router';
import { ThemeToggle } from './ThemeToggle';

export function Header() {
  const tracker = useLocation().pathname === '/tracker';
  return <header className="header"><div className="container header-inner">
    <Link className="brand" to="/" aria-label="Абитуриент — в начало"><span className="brand-mark" aria-hidden="true" />Абитуриент</Link>
    <nav className="navigation" aria-label="Разделы сайта">
      {tracker ? <><Link to="/">О проекте</Link><a href="/#calculator">Калькулятор</a><span aria-current="page">Мои направления</span></> : <><a href="#problem">Проблема</a><a href="#how-it-works">Почему номер не место</a><a href="#calculator">Калькулятор</a><a href="#questions">Вопросы</a></>}
    </nav>
    <div className="header-actions"><ThemeToggle /><a className="button button-primary header-cta" href={tracker ? '/#calculator' : '#calculator'}><span className="desktop-label">Посчитать место</span><span className="mobile-label">Посчитать</span></a></div>
  </div></header>;
}
export function Footer() {
  return <footer className="footer"><div className="container footer-inner"><span>Студенческий проект о поступлении. Материалы основаны на интервью с абитуриентами и репетиторами.</span><Link to="/tracker">Мои направления →</Link></div></footer>;
}
