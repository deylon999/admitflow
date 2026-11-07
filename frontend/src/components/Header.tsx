import { Icon } from './Icons';

export function Header() {
  return (
    <header className="site-header" id="top">
      <div className="header-inner">
        <a className="brand" href="#top" aria-label="AdmitFlow — главная"><span className="brand-mark"/> <span>Абитуриент</span></a>
        <nav className="main-nav" aria-label="Главное меню">
          <a href="#features">Возможности</a>
          <a href="#how-it-works">Как это работает</a>
          <a href="#examples">Примеры</a>
          <a href="#faq">Вопросы</a>
        </nav>
        <div className="header-actions">
          <a href="/auth/login" className="button button-outline button-small">Войти</a>
          <a href="/app/forecast" className="button button-primary button-small">Оценить шансы</a>
        </div>
        <a href="#features" className="mobile-menu" aria-label="Перейти к возможностям"><Icon name="menu" size={19}/></a>
      </div>
    </header>
  );
}
