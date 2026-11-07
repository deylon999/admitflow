import { lazy } from 'react';
import { createBrowserRouter, Link } from 'react-router';
import { LandingPage } from '@/pages/landing';
import { AppShell } from '../ui/AppShell';
import { PageErrorBoundary } from '../ui/PageErrorBoundary';
const TrackerPage = lazy(() => import('@/pages/tracker'));
const SourcesPage = lazy(() => import('@/pages/sources'));
export const router = createBrowserRouter([
  {
    element: (
      <PageErrorBoundary>
        <AppShell />
      </PageErrorBoundary>
    ),
    children: [
      { index: true, element: <LandingPage /> },
      { path: 'tracker', element: <TrackerPage /> },
      { path: 'sources', element: <SourcesPage /> },
      {
        path: '*',
        element: (
          <main
            id="top"
            className="container tracker-page"
          >
            <h1>Страница не найдена</h1>
            <Link
              className="button button-primary"
              to="/"
            >
              На главную
            </Link>
          </main>
        ),
      },
    ],
  },
]);
