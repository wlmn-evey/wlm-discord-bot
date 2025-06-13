import React, { useState, useEffect } from 'react';
import { Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Dashboard from './pages/Dashboard';
import WelcomeWagon from './pages/WelcomeWagon';
import SamReports from './pages/SamReports';
import Configuration from './pages/Configuration';
import ConfigError from './components/ConfigError';

function App() {
  const [status, setStatus] = useState({ loading: true, error: null, missingConfig: [] });

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await fetch('http://localhost:8080/api/status');
        if (!response.ok) {
          throw new Error(`Network response was not ok: ${response.statusText}`);
        }
        const data = await response.json();
        setStatus({ loading: false, error: null, missingConfig: data.missing_config || [] });
      } catch (e) {
        console.error("Failed to fetch bot status:", e);
        setStatus({ loading: false, error: e.message, missingConfig: [] });
      }
    };

    fetchStatus();
  }, []);

  if (status.loading) {
    return <div className="bg-gray-900 text-white h-screen flex items-center justify-center">Loading...</div>;
  }

  if (status.error) {
    return <div className="bg-gray-900 text-white h-screen flex items-center justify-center">Error: {status.error}</div>;
  }

  if (status.missingConfig.length > 0) {
    return <ConfigError missingKeys={status.missingConfig} />;
  }

  return (
    <div className="flex h-screen bg-gray-900 text-white">
      <Sidebar />
      <div className="flex flex-col flex-1">
        <Header />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/welcome-wagon" element={<WelcomeWagon />} />
          <Route path="/sam-reports" element={<SamReports />} />
          <Route path="/configuration" element={<Configuration />} />
        </Routes>
      </div>
    </div>
  );
}

export default App;

