/** Main App component with routing */

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { Layout } from './components/layout/Layout';
import { Dashboard } from './pages/Dashboard';
import { Documents } from './pages/Documents';
import { DocumentDetail } from './components/documents/DocumentDetail';
import { Jobs } from './pages/Jobs';
import { JobDetail } from './pages/JobDetail';
import { Search } from './pages/Search';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000,
      cacheTime: 300000,
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Layout>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/documents" element={<Documents />} />
              <Route path="/documents/:id" element={<DocumentDetail />} />
              <Route path="/jobs" element={<Jobs />} />
              <Route path="/jobs/:id" element={<JobDetail />} />
              <Route path="/search" element={<Search />} />
            </Routes>
          </Layout>
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;
