import { useState } from 'react';
import { Route, Routes } from 'react-router-dom';
import CVEList from './components/CVEList';
import Navbar from './components/Navbar';
import SearchBox from './components/SearchBox';
import TaskManager from './components/TaskManager';
import { DarkModeProvider } from './contexts/DarkModeContext';
import { QueryProvider } from './providers/QueryProvider';

const App: React.FC = () => {
  const [search, setSearch] = useState("");

  const handleSearch = (value: string) => {
    setSearch(value);
  };

  return (
    <DarkModeProvider>
      <QueryProvider>
        {/* Matte Army Green Gradient Background with Dark Mode Support */}
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
              {/* Future: <Route path="/login" element={<Login />} /> */}
            </Routes>
          </div>
        </div>
      </QueryProvider>
    </DarkModeProvider>
  );
};

export default App;
