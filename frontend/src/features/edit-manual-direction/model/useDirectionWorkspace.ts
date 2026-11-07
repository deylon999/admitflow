import { useCallback, useEffect, useRef, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { manualDirectionApi } from '@/entities/manual-direction';
import type { Watch } from '@/entities/manual-direction';
import { sessionApi, sessionAccessKey } from '@/shared/api';
import type { SessionAccess, SessionInfo } from '@/shared/api';
import { clearDraft, readDraft } from './draft-store';
import type { StoredDraft } from './draft-store';

export function useDirectionWorkspace({
  privateVisible,
  expired,
  busy,
  watches,
  sessionInfo,
  onNotice,
}: {
  privateVisible: boolean;
  expired: boolean;
  busy: boolean;
  watches: { data?: Watch[]; isSuccess: boolean };
  sessionInfo?: SessionInfo;
  onNotice: (message: string) => void;
}) {
  const client = useQueryClient();
  const [form, setForm] = useState<'new' | Watch | null>(null);
  const [recovery, setRecovery] = useState<StoredDraft | null>(null);
  const [restored, setRestored] = useState<StoredDraft | null>(null);
  const [focusRequest, setFocusRequest] = useState(0);
  const [returnFocus, setReturnFocus] = useState(false);
  const formOpener = useRef<HTMLButtonElement | null>(null);
  const addButton = useRef<HTMLButtonElement>(null);
  const pageHeading = useRef<HTMLHeadingElement>(null);
  const draftDirty = useRef(false);
  const setDraftDirty = useCallback((dirty: boolean) => {
    draftDirty.current = dirty;
  }, []);
  const canDiscard = () =>
    !draftDirty.current || window.confirm('Удалить несохранённые изменения формы?');

  function openForm(value: 'new' | Watch, button: HTMLButtonElement) {
    const sameForm =
      form === value || (form && form !== 'new' && value !== 'new' && form.id === value.id);
    if (!sameForm && !canDiscard()) return;
    if (!form && recovery && !window.confirm('Заменить сохранённый черновик новой формой?')) return;
    if (!sameForm) {
      clearDraft();
      setRecovery(null);
      setRestored(null);
    }
    formOpener.current = button;
    setReturnFocus(false);
    onNotice('');
    setForm(value);
    setFocusRequest((request) => request + 1);
  }

  function clearWorkspace() {
    clearDraft();
    draftDirty.current = false;
    setRecovery(null);
    setRestored(null);
    setForm(null);
  }

  function closeForm(saved = false) {
    if (!saved && !canDiscard()) return;
    clearWorkspace();
    setReturnFocus(true);
  }

  useEffect(() => {
    if (!returnFocus || busy || form || expired) return;
    const opener = formOpener.current;
    const target =
      opener?.isConnected && !opener.disabled
        ? opener
        : addButton.current && !addButton.current.disabled
          ? addButton.current
          : pageHeading.current;
    target?.focus();
    setReturnFocus(false);
  }, [returnFocus, busy, form, expired]);

  useEffect(() => {
    if (privateVisible && !form && watches.isSuccess && sessionInfo?.draftScope) {
      setRecovery(readDraft(sessionInfo.draftScope, sessionInfo.expiresAt));
    }
  }, [privateVisible, form, watches.isSuccess, watches.data, sessionInfo]);

  useEffect(() => {
    if (!recovery || form) return;
    const timer = setTimeout(
      () => {
        clearDraft();
        setRecovery(null);
        onNotice('Срок хранения черновика закончился. Сохранённые направления не изменены.');
      },
      Math.max(0, recovery.expiresAt - Date.now()),
    );
    return () => clearTimeout(timer);
  }, [recovery, form, onNotice]);

  const restore = useMutation({
    mutationFn: async () => {
      if (!recovery || !sessionInfo?.draftScope) return null;
      const info = await sessionApi.resumeSession();
      if (info.draftScope !== sessionInfo.draftScope) {
        clearDraft();
        setRecovery(null);
        sessionApi.forgetSession();
        client.setQueryData<SessionAccess>(sessionAccessKey, 'changed');
        return null;
      }
      const latest = await manualDirectionApi.list();
      client.setQueryData(['watches'], latest);
      const current = readDraft(info.draftScope, info.expiresAt);
      if (!current) {
        setRecovery(null);
        onNotice('Черновик больше недоступен.');
        return null;
      }
      const watch = current.watchId
        ? latest.find((item) => item.id === current.watchId)
        : undefined;
      if (current.watchId && !watch) {
        onNotice(
          'Направление черновика уже удалено. Поля можно посмотреть перед удалением черновика.',
        );
        return null;
      }
      if (watch && watch.latest.id !== current.baseSnapshotId && !current.intent) {
        onNotice('На сервере более новая версия. Устаревший черновик не восстановлен.');
        return null;
      }
      return { current, watch };
    },
    onSuccess: (result) => {
      if (!result) return;
      setRestored(result.current);
      setForm(result.watch ?? 'new');
      setFocusRequest((value) => value + 1);
      setRecovery(null);
    },
  });

  useEffect(() => {
    if (!expired) return;
    clearDraft();
    draftDirty.current = false;
    setRecovery(null);
    setRestored(null);
    setForm(null);
  }, [expired]);

  function discardRecovery() {
    if (!clearDraft()) {
      onNotice('Не удалось удалить черновик из хранилища вкладки.');
      return;
    }
    setRecovery(null);
    onNotice('Черновик удалён. Сохранённые направления не изменены.');
    requestAnimationFrame(() => addButton.current?.focus());
  }

  const recoveryWatch = recovery?.watchId
    ? watches.data?.find((item) => item.id === recovery.watchId)
    : undefined;
  const recoveryBlocked =
    recovery?.watchId && !recoveryWatch
      ? 'Направление уже удалено.'
      : recoveryWatch && recoveryWatch.latest.id !== recovery?.baseSnapshotId && !recovery?.intent
        ? 'На сервере есть более новое сохранение.'
        : undefined;

  return {
    form,
    recovery,
    restored,
    focusRequest,
    addButton,
    pageHeading,
    setDraftDirty,
    canDiscard,
    openForm,
    closeForm,
    clearWorkspace,
    restore,
    recoveryBlocked,
    discardRecovery,
  };
}
