import type { ReactNode } from 'react';
import { RouteLink } from '../app/RouteLink';
import { PageTitle, Surface } from './UI';

export const authDescriptions = {
    login: 'Войдите, чтобы продолжить работу с вашими направлениями.',
    register: 'Создайте аккаунт и подтвердите email, чтобы сохранить ваши направления.',
    recovery: 'Укажите email — мы отправим инструкции по восстановлению доступа.',
};

export function AuthLayout({ title, description, children }: { title: string; description: string; children: ReactNode }) {
    return <div className="af-auth-layout">
        <div className="af-auth-hero"><RouteLink to="/" className="af-auth-hero__logo">■ Абитуриент</RouteLink><div><span className="af-eyebrow">ADMITFLOW · 2027</span><h1>Поступление —<br />не гадание.</h1><p>Прогнозы, конкурсные списки и твои решения в одной системе.</p></div><span className="af-auth-hero__shape" /></div>
        <main className="af-auth-form-wrap af-auth-panel">
            <PageTitle kicker="ЛИЧНЫЙ КАБИНЕТ" title={title} description={description}/>
            <Surface className="af-auth-card">{children}</Surface>
            <div className="af-auth-preview-link"><RouteLink to="/app">Продолжить без входа ↗</RouteLink></div>
        </main>
    </div>;
}
