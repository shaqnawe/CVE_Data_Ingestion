import { QueryProvider } from './providers/QueryProvider';
import CVEList from './components/CVEList';
import TaskManager from './components/TaskManager';

function App() {
  return (
    <QueryProvider>
      <div className="min-h-screen bg-gray-100">
        <CVEList />
        <TaskManager />
      </div>
    </QueryProvider>
  );
}

export default App;
