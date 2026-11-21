import { useEffect, useState } from 'react';
import { RouteLink } from '../../app/RouteLink';
import { confirmEmail, resetPassword } from '../../shared/account';
import { AuthLayout } from '../../shared/AuthLayout';
import { forgetAuthLink, readAuthLink } from '../../shared/authLink';
import { Action } from '../../shared/UI';
import { PasswordFields, passwordProblem } from './PasswordFields';
import { useSubmission } from './useSubmission';

export function EmailActionPage({ reset }: { reset: boolean }) {
    const path = reset ? '/auth/reset' : '/auth/verify';
    const [token, setToken] = useState(() => readAuthLink(path));
    const [password, setPassword] = useState(''), [confirmation, setConfirmation] = useState('');
    const [complete, setComplete] = useState(false);
    const submission = useSubmission();
    useEffect(() => { forgetAuthLink(); return () => { forgetAuthLink(); }; }, []);
    const title = complete ? reset ? 'Пароль успешно изменён' : 'Email подтверждён' : !token ? 'Нужна новая ссылка' : reset ? 'Новый пароль' : 'Подтвердить email';
    const description = complete ? 'Всё готово для продолжения работы с AdmitFlow.' : !token ? 'Запросите новую ссылку для работы с аккаунтом.' : reset ? 'Придумайте новый пароль для безопасного входа в аккаунт.' : 'Подтвердите адрес из письма, чтобы открыть доступ к аккаунту.';
    return <AuthLayout title={title} description={description}>
        {complete && <div className="af-auth-complete-mark" aria-hidden="true">✓</div>}
        {!token && !complete && <p role="alert" className="af-auth-notice--error">Ссылка недействительна или уже закрыта. Откройте ссылку из письма заново либо запросите новую.</p>}
        {token && <form className="af-auth-form" aria-busy={submission.busy} onSubmit={event => {
            event.preventDefault();
            const problem = reset ? passwordProblem(password, confirmation) : null;
            if (problem) { submission.fail(problem); return; }
            void submission.run(async signal => {
                if (reset) await resetPassword(token, password, signal); else await confirmEmail(token, signal);
                signal.throwIfAborted(); setComplete(true); setToken('');
            }, reset ? 'Войдите с новым паролем, чтобы продолжить работу.' : 'Теперь можно войти в аккаунт и сохранить свои направления.', () => { setPassword(''); setConfirmation(''); });
        }}>
            {reset && <PasswordFields password={password} setPassword={setPassword} confirmation={confirmation} setConfirmation={setConfirmation} busy={submission.busy}/>}
            <button type="submit" className="af-action af-action--primary" disabled={submission.busy}>{submission.busy ? 'Проверяем…' : reset ? 'Сохранить пароль ↗' : 'Подтвердить email ↗'}</button>
        </form>}
        {submission.notices}
        {complete ? <div className="af-auth-complete"><Action to="/auth/login">Войти в аккаунт</Action></div> : <div className="af-auth-links"><RouteLink to="/auth/login">Войти</RouteLink><RouteLink to={reset ? '/auth/recovery' : '/auth/register'}>Запросить новую ссылку</RouteLink></div>}
    </AuthLayout>;
}
