import { QueryProvider } from './providers/QueryProvider';
import CVEList from './components/CVEList';

function App() {
  return (
    <QueryProvider>
      <div className="min-h-screen bg-gray-100">
        <CVEList />
      </div>
    </QueryProvider>
  );
}

export default App;
