import { useEffect, useRef, useState, type ReactNode } from 'react';
import { RouteLink } from '../app/RouteLink';
import { navigate } from '../app/navigation';
import { ApiError } from '../shared/api';
import { confirmEmail, login, logout, resetPassword, retryAccount, sendAccountEmail } from '../shared/account';
import { forgetAuthLink, readAuthLink } from '../shared/authLink';
import { useAccount } from '../shared/useAccount';
import { Action, EmptyMessage, PageTitle, Surface } from '../shared/UI';

function AuthFrame({ title, children }: { title: string; children: ReactNode }) {
    return <div className="af-auth-layout">
        <div className="af-auth-hero"><RouteLink to="/" className="af-auth-hero__logo">■ Абитуриент</RouteLink><div><span className="af-eyebrow">ADMITFLOW · 2027</span><h1>Поступление —<br />не гадание.</h1><p>Прогнозы, конкурсные списки и твои решения в одной системе.</p></div><span className="af-auth-hero__shape" /></div>
        <div className="af-auth-form-wrap"><PageTitle kicker="ЛИЧНЫЙ КАБИНЕТ" title={title} description="Войдите, чтобы продолжить работу с направлениями."/><Surface>{children}</Surface><div className="af-auth-preview-link"><Action to="/app" variant="outline">Продолжить без входа ↗</Action></div></div>
    </div>;
}
function useSubmission() {
    const [busy, setBusy] = useState(false), [message, setMessage] = useState(''), [failure, setFailure] = useState('');
    const controller = useRef<AbortController | null>(null), active = useRef(false), pending = useRef(false);
    useEffect(() => { active.current = true; return () => { active.current = false; controller.current?.abort(); }; }, []);
    async function run(operation: (signal: AbortSignal) => Promise<void>, success: string, clear?: () => void) {
        if (pending.current) return;
        pending.current = true; setBusy(true); setMessage(''); setFailure('');
        const abort = new AbortController(); controller.current = abort;
        try {
            await operation(abort.signal);
            if (active.current) setMessage(success);
        } catch (error) {
            if (active.current && !abort.signal.aborted) setFailure(error instanceof ApiError ? error.message + (error.retryAfter ? ` Повторите через ${error.retryAfter} сек.` : '') : 'Не удалось выполнить запрос. Повторите позже.');
        } finally {
            pending.current = false;
            if (active.current) { setBusy(false); clear?.(); }
        }
    }
    return { busy, run, fail: setFailure, notices: <>{failure && <p role="alert">{failure}</p>}{message && <p role="status" className="af-inline-success">{message}</p>}</> };
}
export function passwordProblem(password: string, confirmation: string): string | null {
    const length = Array.from(password).length;
    if (length < 15 || length > 128 || new TextEncoder().encode(password).length > 512) return 'Пароль должен содержать от 15 до 128 символов. Можно использовать пробелы и длинные фразы.';
    return password !== confirmation ? 'Пароли не совпадают.' : null;
}
function PasswordFields({ password, setPassword, confirmation, setConfirmation, busy, loginMode = false }: { password: string; setPassword: (value: string) => void; confirmation: string; setConfirmation: (value: string) => void; busy: boolean; loginMode?: boolean }) {
    return <><label className="af-field"><span>ПАРОЛЬ</span><input type="password" value={password} onChange={e => setPassword(e.target.value)} autoComplete={loginMode ? 'current-password' : 'new-password'} placeholder={loginMode ? 'Твой пароль' : 'Не менее 15 символов'} required disabled={busy}/></label>{!loginMode && <label className="af-field"><span>ПОДТВЕРЖДЕНИЕ ПАРОЛЯ</span><input type="password" value={confirmation} onChange={e => setConfirmation(e.target.value)} autoComplete="new-password" placeholder="Повтори пароль" required disabled={busy}/></label>}</>;
}
const genericNotice = 'Запрос принят. Если адрес подходит для этой операции, вы получите письмо. Проверьте почту и папку «Спам».';
export function AuthPage({ mode }: { mode: 'login' | 'register' | 'recovery' }) {
    const [email, setEmail] = useState(''), [password, setPassword] = useState(''), [confirmation, setConfirmation] = useState('');
    const submission = useSubmission();
    const clear = () => { setPassword(''); setConfirmation(''); };
    const title = mode === 'login' ? 'С возвращением!' : mode === 'register' ? 'Создать аккаунт' : 'Восстановить доступ';
    return <AuthFrame title={title}>
        <form className="af-auth-form" onSubmit={event => {
            event.preventDefault();
            const problem = mode === 'register' ? passwordProblem(password, confirmation) : mode === 'login' && (Array.from(password).length > 128 || new TextEncoder().encode(password).length > 512) ? 'Пароль слишком длинный.' : null;
            if (problem) { submission.fail(problem); return; }
            void submission.run(async signal => {
                if (mode === 'login') { await login(email, password, signal); signal.throwIfAborted(); navigate('/app/profile'); }
                else await sendAccountEmail(mode === 'register' ? 'register' : 'recovery/request', email, mode === 'register' ? password : undefined, signal);
            }, mode === 'login' ? '' : genericNotice, clear);
        }}>
            <label className="af-field"><span>EMAIL</span><input type="email" placeholder="you@example.com" value={email} onChange={e => setEmail(e.target.value)} autoComplete="email" maxLength={320} required disabled={submission.busy}/></label>
            {mode !== 'recovery' && <PasswordFields password={password} setPassword={setPassword} confirmation={confirmation} setConfirmation={setConfirmation} busy={submission.busy} loginMode={mode === 'login'}/>}
            <button type="submit" className="af-action af-action--primary" disabled={submission.busy}>{submission.busy ? 'Отправляем…' : mode === 'login' ? 'Войти ↗' : mode === 'register' ? 'Создать аккаунт ↗' : 'Получить инструкцию ↗'}</button>
        </form>
        {submission.notices}
        {mode !== 'recovery' && <p><button type="button" className="af-action af-action--outline" disabled={submission.busy} onClick={() => {
            if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) || email.length > 320) { submission.fail('Введите email для повторного подтверждения.'); return; }
            void submission.run(signal => sendAccountEmail('verification/request', email, undefined, signal).then(() => {}), genericNotice, clear);
        }}>Повторить письмо подтверждения</button></p>}
        <div className="af-auth-links">{mode !== 'login' && <RouteLink to="/auth/login">Войти</RouteLink>}{mode !== 'register' && <RouteLink to="/auth/register">Зарегистрироваться</RouteLink>}{mode !== 'recovery' && <RouteLink to="/auth/recovery">Забыли пароль?</RouteLink>}</div>
    </AuthFrame>;
}
export function EmailActionPage({ reset }: { reset: boolean }) {
    const path = reset ? '/auth/reset' : '/auth/verify';
    const [token, setToken] = useState(() => readAuthLink(path));
    const [password, setPassword] = useState(''), [confirmation, setConfirmation] = useState('');
    const [complete, setComplete] = useState(false);
    const submission = useSubmission();
    useEffect(() => { forgetAuthLink(); return () => { forgetAuthLink(); }; }, []);
    return <AuthFrame title={reset ? 'Новый пароль' : 'Подтвердить email'}>
        {!token && !complete && <p role="alert">Ссылка недействительна или уже закрыта. Откройте ссылку из письма заново либо запросите новую.</p>}
        {token && <form className="af-auth-form" onSubmit={event => {
            event.preventDefault();
            const problem = reset ? passwordProblem(password, confirmation) : null;
            if (problem) { submission.fail(problem); return; }
            void submission.run(async signal => {
                if (reset) await resetPassword(token, password, signal); else await confirmEmail(token, signal);
                signal.throwIfAborted(); setComplete(true); setToken('');
            }, reset ? 'Пароль изменён. Войдите с новым паролем.' : 'Email подтверждён. Теперь можно войти.', () => { setPassword(''); setConfirmation(''); });
        }}>
            {reset && <PasswordFields password={password} setPassword={setPassword} confirmation={confirmation} setConfirmation={setConfirmation} busy={submission.busy}/>}
            <button type="submit" className="af-action af-action--primary" disabled={submission.busy}>{submission.busy ? 'Проверяем…' : reset ? 'Сохранить пароль ↗' : 'Подтвердить email ↗'}</button>
        </form>}
        {submission.notices}<div className="af-auth-links"><RouteLink to="/auth/login">Войти</RouteLink><RouteLink to={reset ? '/auth/recovery' : '/auth/register'}>Запросить новую ссылку</RouteLink></div>
    </AuthFrame>;
}
export function AccountPage() {
    const account = useAccount(), submission = useSubmission();
    if (account.status === 'idle' || account.status === 'checking') return <div role="status"><EmptyMessage title="Проверяем аккаунт" description="Подтверждаем доступ на сервере."/></div>;
    if (account.status === 'error') return <div role="alert"><EmptyMessage title="Не удалось проверить аккаунт" description={account.error.message} action={<><button type="button" className="af-action af-action--primary" onClick={retryAccount}>Повторить</button><Action to="/auth/login" variant="outline">Войти</Action></>}/></div>;
    if (account.status !== 'authenticated') return <EmptyMessage title="Войдите в аккаунт" description="Гостевые направления доступны без входа. Для аккаунта подтвердите email и войдите." action={<Action to="/auth/login">Войти ↗</Action>}/>;
    return <><PageTitle kicker="ЛИЧНЫЙ КАБИНЕТ" title="Мой аккаунт" description="Доступ подтверждён сервером."/><Surface title="Email подтверждён"><p>{account.session.account.email}</p><button type="button" className="af-action af-action--outline" disabled={submission.busy} onClick={() => void submission.run(() => logout(), '')}>Выйти из аккаунта</button>{submission.notices}</Surface></>;
}
