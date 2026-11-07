import { useEffect, useRef, useState } from 'react';
import { useIsMutating, useQuery } from '@tanstack/react-query';
import { manualDirectionApi, selectWatches } from '@/entities/manual-direction';
import type { WatchOrder } from '@/entities/manual-direction';
import { sourceApi } from '@/entities/admission-source';
import { useDirectionWorkspace } from '@/features/edit-manual-direction';
import { useManualExport } from '@/features/export-manual-directions';
import { useGuestSessionActions } from '@/features/manage-guest-session';
import { useManualReportPrint } from '@/features/print-manual-directions';
import { sessionApi, SessionExpiredError, useSessionAccess } from '@/shared/api';

export function useTrackerModel() {
  const [search, setSearch] = useState('');
  const [scenario, setScenario] = useState('all');
  const [order, setOrder] = useState<WatchOrder>('updated');
  const [notice, setNotice] = useState('');
  const [confirmReset, setConfirmReset] = useState(false);
  const resetButton = useRef<HTMLButtonElement>(null);
  const busy = useIsMutating() > 0;
  const resetting = useIsMutating({ mutationKey: ['session-reset'] }) > 0;
  const access = useSessionAccess();
  const changed = access.data === 'changed';
  const watches = useQuery({
    queryKey: ['watches'],
    queryFn: ({ signal }) => manualDirectionApi.list(signal),
    enabled: !changed && !resetting,
    staleTime: 0,
    refetchOnWindowFocus: true,
  });
  const expired =
    changed || access.data === 'expired' || watches.error instanceof SessionExpiredError;
  const privateVisible = !expired && !resetting;
  const sessionInfo = useQuery({
    queryKey: ['session-info'],
    queryFn: sessionApi.session,
    enabled: privateVisible,
    staleTime: Infinity,
  });
  const editor = useDirectionWorkspace({
    privateVisible,
    expired,
    busy,
    watches,
    sessionInfo: sessionInfo.data,
    onNotice: setNotice,
  });
  useEffect(() => {
    if (!expired) return;
    setConfirmReset(false);
    setNotice('');
  }, [expired]);
  const download = useManualExport();
  const { synchronize, reset } = useGuestSessionActions({
    beforeReset: editor.clearWorkspace,
    onSynchronized: () => {
      download.reset();
      requestAnimationFrame(() => editor.addButton.current?.focus());
    },
    onResetSettled: () => download.reset(),
    onResetSuccess: () => {
      setConfirmReset(false);
      setNotice('Создана новая гостевая сессия.');
      requestAnimationFrame(() => editor.addButton.current?.focus());
    },
    onResetError: () => {
      setConfirmReset(false);
      setNotice('');
    },
  });
  const budget = useQuery({
    queryKey: ['direction-budget'],
    queryFn: ({ signal }) => sourceApi.directionBudget(signal),
    enabled: privateVisible,
  });
  // Same query/cache as the archive panel; its result is needed before declaring the list empty.
  const archive = useQuery({
    queryKey: ['archive-directions'],
    queryFn: ({ signal }) => sourceApi.subscriptions(signal),
    enabled: privateVisible && access.data === 'active',
  });
  const directionsLoading = watches.isPending || (watches.data?.length === 0 && archive.isPending);
  const directionsError =
    (watches.isError && watches.data === undefined) ||
    (watches.data?.length === 0 && archive.isError && archive.data === undefined);
  const directionsEmpty =
    watches.isSuccess &&
    watches.data.length === 0 &&
    archive.isSuccess &&
    archive.data.length === 0;
  const refreshError =
    !directionsError &&
    ((watches.isError && watches.data !== undefined) ||
      (archive.isError && archive.data !== undefined));
  const directionTotal = privateVisible
    ? Math.max(budget.data?.total ?? 0, watches.data?.length ?? 0)
    : 0;
  const count = privateVisible ? (watches.data?.length ?? 0) : 0;
  const visible = selectWatches(
    privateVisible ? (watches.data ?? []) : [],
    search,
    scenario,
    order,
  );
  const report = useManualReportPrint();
  async function refreshDirections() {
    setNotice('');
    const results = await Promise.all([watches.refetch(), archive.refetch(), budget.refetch()]);
    if (results.every((result) => !result.error)) {
      setNotice('Список направлений обновлён. Ручные цифры обновляете вы.');
    }
  }
  function clearFilters() {
    setSearch('');
    setScenario('all');
    setOrder('updated');
  }
  return {
    search,
    setSearch,
    scenario,
    setScenario,
    order,
    setOrder,
    notice,
    setNotice,
    confirmReset,
    setConfirmReset,
    resetButton,
    busy,
    resetting,
    changed,
    watches,
    expired,
    privateVisible,
    sessionInfo,
    editor,
    download,
    synchronize,
    reset,
    budget,
    archive,
    directionsLoading,
    directionsError,
    directionsEmpty,
    refreshError,
    directionTotal,
    count,
    visible,
    report,
    refreshDirections,
    clearFilters,
  };
}

export type TrackerModel = ReturnType<typeof useTrackerModel>;
