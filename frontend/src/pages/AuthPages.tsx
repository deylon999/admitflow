import { useState } from 'react';
import { RouteLink } from '../app/RouteLink';
import { Action, PageTitle, Surface } from '../shared/UI';

export function AuthPage({ mode }: { mode: 'login' | 'register' | 'recovery' }) {
  const [sent, setSent] = useState(false);
  const titles = {
    login: 'С возвращением!',
    register: 'Создать аккаунт',
    recovery: 'Восстановить доступ',
  };

  return (
    <div className="af-auth-layout">
      <div className="af-auth-hero">
        <RouteLink to="/" className="af-auth-hero__logo">■ Абитуриент</RouteLink>
        <div>
          <span className="af-eyebrow">ADMITFLOW · 2027</span>
          <h1>Поступление —<br />не гадание.</h1>
          <p>Прогнозы, конкурсные списки и твои решения в одной системе.</p>
        </div>
        <span className="af-auth-hero__shape" />
      </div>
      <div className="af-auth-form-wrap">
        <PageTitle kicker="ЛИЧНЫЙ КАБИНЕТ" title={titles[mode]} description="Войдите, чтобы продолжить работу с направлениями." />
        <Surface>
          <form className="af-auth-form" onSubmit={e => { e.preventDefault(); setSent(true); }}>
            <label className="af-field"><span>EMAIL</span><input type="email" placeholder="you@example.com" required /></label>
            {mode !== 'recovery' && <label className="af-field"><span>ПАРОЛЬ</span><input type="password" placeholder="Не менее 8 символов" minLength={8} required /></label>}
            {mode === 'register' && <label className="af-field"><span>ПОДТВЕРЖДЕНИЕ ПАРОЛЯ</span><input type="password" placeholder="Повтори пароль" minLength={8} required /></label>}
            <button type="submit" className="af-action af-action--primary">{mode === 'login' ? 'Войти ↗' : mode === 'register' ? 'Создать аккаунт ↗' : 'Получить инструкцию ↗'}</button>
          </form>
          {sent && <p role="status" className="af-inline-success">В этой версии вход пока не подключён.</p>}
          <div className="af-auth-links">
            {mode !== 'login' && <RouteLink to="/auth/login">Войти</RouteLink>}
            {mode !== 'register' && <RouteLink to="/auth/register">Зарегистрироваться</RouteLink>}
            {mode !== 'recovery' && <RouteLink to="/auth/recovery">Забыли пароль?</RouteLink>}
          </div>
        </Surface>
        <div className="af-auth-preview-link"><Action to="/app" variant="outline">Продолжить без входа ↗</Action></div>
      </div>
    </div>
  );
}
