export function passwordProblem(password: string, confirmation: string): string | null {
    const length = Array.from(password).length;
    if (length < 15 || length > 128 || new TextEncoder().encode(password).length > 512) return 'Пароль должен содержать от 15 до 128 символов. Можно использовать пробелы и длинные фразы.';
    return password !== confirmation ? 'Пароли не совпадают.' : null;
}
export function PasswordFields({ password, setPassword, confirmation, setConfirmation, busy, loginMode = false }: { password: string; setPassword: (value: string) => void; confirmation: string; setConfirmation: (value: string) => void; busy: boolean; loginMode?: boolean }) {
    return <><label className="af-field"><span>ПАРОЛЬ</span><input type="password" value={password} onChange={e => setPassword(e.target.value)} autoComplete={loginMode ? 'current-password' : 'new-password'} placeholder={loginMode ? 'Твой пароль' : 'Не менее 15 символов'} required disabled={busy}/></label>{!loginMode && <label className="af-field"><span>ПОДТВЕРЖДЕНИЕ ПАРОЛЯ</span><input type="password" value={confirmation} onChange={e => setConfirmation(e.target.value)} autoComplete="new-password" placeholder="Повтори пароль" required disabled={busy}/></label>}</>;
}
