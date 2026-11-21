import { useEffect, useRef, useState } from 'react';
import { ApiError } from '../../shared/api';

export type SubmissionNotice = { text: string; kind: 'success' | 'neutral' };
export function useSubmission() {
    const [busy, setBusy] = useState(false), [message, setMessage] = useState<SubmissionNotice | null>(null), [failure, setFailure] = useState<{ id: number; text: string } | null>(null);
    const noticeId = useRef(0);
    function fail(text: string) {
        setMessage(null);
        setFailure({ id: ++noticeId.current, text });
    }
    const controller = useRef<AbortController | null>(null), active = useRef(false), pending = useRef(false);
    useEffect(() => { active.current = true; return () => { active.current = false; controller.current?.abort(); }; }, []);
    async function run(operation: (signal: AbortSignal) => Promise<void | SubmissionNotice>, success: string, clear?: () => void) {
        if (pending.current) return;
        pending.current = true; setBusy(true); setMessage(null); setFailure(null);
        const abort = new AbortController(); controller.current = abort;
        try {
            const result = await operation(abort.signal);
            if (active.current) setMessage(result ?? (success ? { text: success, kind: 'success' } : null));
        } catch (error) {
            if (active.current && !abort.signal.aborted) fail(error instanceof ApiError ? error.message + (error.retryAfter ? ` Повторите через ${error.retryAfter} сек.` : '') : 'Не удалось выполнить запрос. Повторите позже.');
        } finally {
            pending.current = false;
            if (active.current) { setBusy(false); clear?.(); }
        }
    }
    return { busy, run, fail, notices: <>{failure && <p key={failure.id} role="alert" className="af-auth-notice--error">{failure.text}</p>}{message && <p role="status" className={message.kind === 'success' ? 'af-inline-success' : 'af-auth-notice--neutral'}>{message.text}</p>}</> };
}
