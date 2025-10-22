import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Dashboard } from './components/Dashboard';
import { HotTopics } from './components/HotTopics';
import { AdminPanel } from './components/AdminPanel';
import { ErrorBoundary } from './components/ErrorBoundary';

function App() {
  return (
    <ErrorBoundary>
      <Router>
        <div className="min-h-screen bg-gradient-to-br from-dark-bg via-dark-surface to-dark-bg">
          {/* Navigation */}
          <nav className="glass-card-strong border-b border-glass-border-strong">
            <div className="container mx-auto px-6">
              <div className="flex items-center justify-between h-16">
                <div className="flex items-center">
                  <h1 className="text-2xl font-bold bg-gradient-to-r from-emerald-400 to-blue-500 bg-clip-text text-transparent">
                    Reddit Sentiment Analysis
                  </h1>
                </div>
                <div className="flex space-x-2">
                  <Link
                    to="/"
                    className="px-4 py-2 rounded-lg hover:bg-dark-elevated/60 transition-all text-gray-200 hover:text-white font-medium"
                  >
                    Dashboard
                  </Link>
                  <Link
                    to="/hot-topics"
                    className="px-4 py-2 rounded-lg hover:bg-dark-elevated/60 transition-all text-gray-200 hover:text-white font-medium"
                  >
                    Hot Topics
                  </Link>
                  <Link
                    to="/admin"
                    className="px-4 py-2 rounded-lg bg-orange-600/20 hover:bg-orange-600/30 transition-all text-orange-400 hover:text-orange-300 font-semibold border border-orange-600/30"
                  >
                    Admin
                  </Link>
                </div>
              </div>
            </div>
          </nav>

          {/* Routes */}
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/hot-topics" element={<HotTopics />} />
            <Route path="/admin" element={<AdminPanel />} />
          </Routes>
        </div>
      </Router>
    </ErrorBoundary>
  );
}

export default App;
