import { Suspense, useEffect } from 'react';
import { Outlet } from 'react-router';
import { sessionApi, sessionChangeKey, sessionAccessKey } from '@/shared/api';
import { clearDraft } from '@/features/edit-manual-direction';
import { privateQueryFamilies } from '@/features/manage-guest-session';
import { queryClient } from '../providers/query-client';
import { PagePosition } from '../routes/PagePosition';
import { Header, Footer } from './Layout';
import { Card } from '@/shared/ui';
export function AppShell() {
  useEffect(() => {
    const onStorage = (event: StorageEvent) => {
      if (event.key !== sessionChangeKey) return;
      clearDraft();
      sessionApi.forgetSession();
      queryClient.setQueryData(sessionAccessKey, 'changed');
      for (const key of privateQueryFamilies) void queryClient.cancelQueries({ queryKey: [key] });
    };
    window.addEventListener('storage', onStorage);
    return () => window.removeEventListener('storage', onStorage);
  }, []);
  return (
    <>
      <PagePosition />
      <a
        className="skip-link"
        href="#top"
        onClick={() => {
          const main = document.querySelector('main');
          if (main) {
            main.tabIndex = -1;
            main.focus();
          }
        }}
      >
        Перейти к содержимому
      </a>
      <Header />
      <Suspense
        fallback={
          <main
            id="top"
            className="container page-shell"
          >
            <Card
              className="page-message"
              aria-busy="true"
            >
              <p role="status">Загружаем страницу…</p>
            </Card>
          </main>
        }
      >
        <Outlet />
      </Suspense>
      <Footer />
    </>
  );
}
