import { useState } from 'react';
import { RouteLink } from '../../app/RouteLink';
import { AuthLayout } from '../../shared/AuthLayout';

export function DemoAuthPage({ mode }: { mode: 'login' | 'register' | 'recovery' }) {
  const [sent, setSent] = useState(false);
  const titles = {
    login: 'С возвращением!',
    register: 'Создать аккаунт',
    recovery: 'Восстановить доступ',
  };

  return (
    <AuthLayout title={titles[mode]} description="Демонстрационная форма. Вход и отправка писем здесь не выполняются.">
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
    </AuthLayout>
  );
}

// Demo shares presentation only and never calls account endpoints.
