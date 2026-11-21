import { useEffect, useState } from 'react';
import { RouteLink } from '../../app/RouteLink';
import { navigate } from '../../app/navigation';
import { login, sendAccountEmail } from '../../shared/account';
import { ApiError } from '../../shared/api';
import { AuthLayout, authDescriptions } from '../../shared/AuthLayout';
import { PasswordFields, passwordProblem } from './PasswordFields';
import { useSubmission, type SubmissionNotice } from './useSubmission';

const genericNotice = 'Запрос принят. Если адрес подходит для этой операции, вы получите письмо. Проверьте почту и папку «Спам».';
const dispatchNotice = 'Запрос принят. Почтовый сервер принял письмо для этого адреса. Проверьте почту и папку «Спам». Если письмо не пришло, запросите его повторно.';
const suppressedNotice = 'Запрос принят, но письмо сейчас не отправлено из-за ограничения частоты. Повторите запрос через час.';
const resendLabel = 'Отправить письмо повторно';
const cooldownLabel = 'Повторная отправка доступна через';
export function AuthPage({ mode }: { mode: 'login' | 'register' | 'recovery' }) {
    const [email, setEmail] = useState(''), [password, setPassword] = useState(''), [confirmation, setConfirmation] = useState('');
    const submission = useSubmission();
    const [mailStage, setMailStage] = useState<{ email: string; notBefore: number } | null>(null);
    const [now, setNow] = useState(Date.now);
    const remaining = mailStage ? Math.max(0, Math.ceil((mailStage.notBefore - now) / 1000)) : 0;
    useEffect(() => {
        if (!mailStage) return;
        const timer = setInterval(() => setNow(Date.now()), 1000);
        return () => clearInterval(timer);
    }, [mailStage]);
    async function requestEmail(kind: 'register' | 'verification/request' | 'recovery/request', signal: AbortSignal): Promise<SubmissionNotice> {
        const result = await sendAccountEmail(kind, email, kind === 'register' ? password : undefined, signal);
        signal.throwIfAborted();
        if (result?.dispatch === 'accepted' && kind !== 'recovery/request') {
            const receivedAt = Date.now();
            setNow(receivedAt);
            setMailStage({ email, notBefore: receivedAt + result.retryAfterSeconds * 1000 });
        }
        if (kind === 'verification/request' && result?.dispatch !== 'accepted') {
            setMailStage(stage => stage ? { ...stage, notBefore: Date.now() + (result?.retryAfterSeconds ?? 60) * 1000 } : null);
        }
        if (!result) return { text: genericNotice, kind: 'neutral' };
        return result.dispatch === 'accepted'
            ? { text: dispatchNotice, kind: 'success' }
            : { text: suppressedNotice, kind: 'neutral' };
    }
    const clear = () => { setPassword(''); setConfirmation(''); };
    const title = mode === 'login' ? 'С возвращением!' : mode === 'register' ? 'Создать аккаунт' : 'Восстановить доступ';
    return <AuthLayout title={title} description={authDescriptions[mode]}>
        <form className="af-auth-form" aria-busy={submission.busy} onSubmit={event => {
            event.preventDefault();
            const problem = mode === 'register' ? passwordProblem(password, confirmation) : mode === 'login' && (Array.from(password).length > 128 || new TextEncoder().encode(password).length > 512) ? 'Пароль слишком длинный.' : null;
            if (problem) { submission.fail(problem); return; }
            setMailStage(null);
            void submission.run(async signal => {
                if (mode === 'login') { await login(email, password, signal); signal.throwIfAborted(); navigate('/app/profile'); }
                else return requestEmail(mode === 'register' ? 'register' : 'recovery/request', signal);
            }, mode === 'login' ? '' : genericNotice, clear);
        }}>
            <label className="af-field"><span>EMAIL</span><input type="email" placeholder="you@example.com" value={email} onChange={e => { setEmail(e.target.value); setMailStage(null); }} autoComplete="email" maxLength={320} required disabled={submission.busy}/></label>
            {mode !== 'recovery' && <PasswordFields password={password} setPassword={setPassword} confirmation={confirmation} setConfirmation={setConfirmation} busy={submission.busy} loginMode={mode === 'login'}/>}
            <button type="submit" className="af-action af-action--primary" disabled={submission.busy}>{submission.busy ? 'Отправляем…' : mode === 'login' ? 'Войти ↗' : mode === 'register' ? 'Создать аккаунт ↗' : 'Получить инструкцию ↗'}</button>
        </form>
        {submission.notices}
        {mode === 'register' && mailStage?.email === email && <div className="af-auth-resend">
            <button type="button" className="af-action af-action--outline" disabled={submission.busy || remaining > 0} onClick={() => {
                if (submission.busy || remaining > 0) return;
                void submission.run(async signal => {
                    try {
                        return await requestEmail('verification/request', signal);
                    } catch (error) {
                        if (!signal.aborted) setMailStage(stage => stage ? { ...stage, notBefore: Date.now() + Math.max(60, error instanceof ApiError ? error.retryAfter ?? 0 : 0) * 1000 } : null);
                        throw error;
                    }
                }, '', clear);
            }}>{resendLabel}</button>
            {remaining > 0 && <p className="af-auth-resend__hint">{cooldownLabel} {remaining} сек.</p>}
        </div>}
        <div className="af-auth-links">{mode !== 'login' && <RouteLink to="/auth/login">Войти</RouteLink>}{mode !== 'register' && <RouteLink to="/auth/register">Зарегистрироваться</RouteLink>}{mode !== 'recovery' && <RouteLink to="/auth/recovery">Забыли пароль?</RouteLink>}</div>
    </AuthLayout>;
}
