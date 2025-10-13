import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Dashboard } from './components/Dashboard';
import { HotTopics } from './components/HotTopics';
import './App.css';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        {/* Navigation */}
        <nav className="bg-white shadow-md">
          <div className="container mx-auto px-4">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center">
                <h1 className="text-xl font-bold text-gray-800">
                  Reddit Sentiment Analysis
                </h1>
              </div>
              <div className="flex space-x-4">
                <Link
                  to="/"
                  className="px-4 py-2 rounded hover:bg-gray-100 transition"
                >
                  Dashboard
                </Link>
                <Link
                  to="/hot-topics"
                  className="px-4 py-2 rounded hover:bg-gray-100 transition"
                >
                  Hot Topics
                </Link>
              </div>
            </div>
          </div>
        </nav>

        {/* Routes */}
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/hot-topics" element={<HotTopics />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
