import { QueryClientProvider } from '@tanstack/react-query';
import { RouterProvider } from 'react-router';
import { queryClient } from './providers/query-client';
import { router } from './routes/router';
import './styles/tokens.css';
import './styles/base.css';
import './styles/styles.css';
import './styles/tracker.css';
import '@/shared/ui/ui.css';
import './styles/print.css';
export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  );
}
