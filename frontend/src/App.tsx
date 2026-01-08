import { useState } from 'react';
import { Route, Routes } from 'react-router-dom';
import CVEList from './components/CVEList';
import Navbar from './components/Navbar';
import SearchBox from './components/SearchBox';
import TaskManager from './components/TaskManager';
import AuthPage from './components/AuthPage';
import { DarkModeProvider } from './contexts/DarkModeContext';
import { QueryProvider } from './providers/QueryProvider';
import { AuthProvider } from './contexts/AuthContext';
import { useAuth } from './hooks/useAuth';

const AppContent: React.FC = () => {
  const [search, setSearch] = useState("");
  const { user, isLoading } = useAuth();

  const handleSearch = (value: string) => {
    setSearch(value);
  };

  // Show loading spinner while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#4B5320] via-[#6B8E23] to-[#3D442D] dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  // Show auth page if not authenticated
  if (!user) {
    return <AuthPage />;
  }

  // Show main app if authenticated
  return (
    <div className="min-h-screen bg-gradient-to-br from-[#4B5320] via-[#6B8E23] to-[#3D442D] dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      <Navbar />
      <div className="max-w-6xl mx-auto py-8 px-4">
        <Routes>
          <Route
            path="/"
            element={
              <>
                <SearchBox value={search} onChange={handleSearch} placeholder="Search CVEs by keyword or ID." />
                <CVEList search={search} />
              </>
            }
          />
          <Route path="/tasks" element={<TaskManager />} />
        </Routes>
      </div>
    </div>
  );
};

const App: React.FC = () => {
  return (
    <DarkModeProvider>
      <AuthProvider>
        <QueryProvider>
          <AppContent />
        </QueryProvider>
      </AuthProvider>
    </DarkModeProvider>
  );
};

export default App;
