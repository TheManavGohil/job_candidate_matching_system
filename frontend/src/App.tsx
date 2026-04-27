import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Navbar from './components/Navbar';
import HomePage from './pages/HomePage';
import JobsPage from './pages/JobsPage';
import JobDetailPage from './pages/JobDetailPage';
import UploadPage from './pages/UploadPage';
import CandidatesPage from './pages/CandidatesPage';
import MatchResultsPage from './pages/MatchResultsPage';
import CandidateDetailPage from './pages/CandidateDetailPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-bg">
          <Navbar />
          <main>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/jobs" element={<JobsPage />} />
              <Route path="/jobs/:jdId" element={<JobDetailPage />} />
              <Route path="/upload" element={<UploadPage />} />
              <Route path="/candidates" element={<CandidatesPage />} />
              <Route path="/match/:jdId" element={<MatchResultsPage />} />
              <Route path="/match/:jdId/:candidateId" element={<CandidateDetailPage />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
