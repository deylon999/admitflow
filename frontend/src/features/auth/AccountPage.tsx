import { logout, retryAccount } from '../../shared/account';
import { Action, EmptyMessage, PageTitle, Surface } from '../../shared/UI';
import { useAccount } from '../../shared/useAccount';
import { useSubmission } from './useSubmission';

export function AccountPage() {
    const account = useAccount(), submission = useSubmission();
    if (account.status === 'idle' || account.status === 'checking') return <div role="status"><EmptyMessage title="Проверяем аккаунт" description="Подтверждаем доступ на сервере."/></div>;
    if (account.status === 'error') return <div role="alert"><EmptyMessage title="Не удалось проверить аккаунт" description={account.error.message} action={<><button type="button" className="af-action af-action--primary" onClick={retryAccount}>Повторить</button><Action to="/auth/login" variant="outline">Войти</Action></>}/></div>;
    if (account.status !== 'authenticated') return <EmptyMessage title="Войдите в аккаунт" description="Гостевые направления доступны без входа. Для аккаунта подтвердите email и войдите." action={<Action to="/auth/login">Войти ↗</Action>}/>;
    return <><PageTitle kicker="ЛИЧНЫЙ КАБИНЕТ" title="Мой аккаунт" description="Доступ подтверждён сервером."/><Surface title="Email подтверждён"><p style={{ overflowWrap: 'anywhere' }}>{account.session.account.email}</p><button type="button" className="af-action af-action--outline" disabled={submission.busy} onClick={() => void submission.run(() => logout(), '')}>Выйти из аккаунта</button>{submission.notices}</Surface></>;
}
