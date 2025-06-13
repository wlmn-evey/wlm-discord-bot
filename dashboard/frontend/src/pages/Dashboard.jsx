import React from 'react';

function Dashboard() {
  return (
    <main className="flex-1 p-8">
      <h1 className="text-3xl font-bold text-white mb-6">Dashboard Overview</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Placeholder cards */}
        <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
          <h2 className="text-xl font-semibold text-white">Active Members</h2>
          <p className="text-4xl font-bold text-green-400 mt-2">128</p>
        </div>
        <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
          <h2 className="text-xl font-semibold text-white">New In Town</h2>
          <p className="text-4xl font-bold text-blue-400 mt-2">12</p>
        </div>
        <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
          <h2 className="text-xl font-semibold text-white">Open Flags</h2>
          <p className="text-4xl font-bold text-red-400 mt-2">3</p>
        </div>
      </div>
    </main>
  );
}

export default Dashboard;
