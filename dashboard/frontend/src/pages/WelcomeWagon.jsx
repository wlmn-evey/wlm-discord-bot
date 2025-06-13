import React, { useState, useEffect } from 'react';

function WelcomeWagon() {
  const [newMembers, setNewMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchNewMembers = async () => {
      try {
        setLoading(true);
        const response = await fetch('http://localhost:8080/api/welcome-wagon/new-members');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setNewMembers(data);
      } catch (e) {
        setError(e.message);
        console.error("Failed to fetch new members:", e);
      } finally {
        setLoading(false);
      }
    };

    fetchNewMembers();
  }, []);

  const formatDate = (isoString) => {
    if (!isoString) return 'N/A';
    return new Date(isoString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  return (
    <main className="flex-1 p-8">
      <h1 className="text-3xl font-bold text-white mb-6">Welcome Wagon</h1>
      <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
        {loading && <p className="text-white">Loading new members...</p>}
        {error && <p className="text-red-400">Error: {error}</p>}
        {!loading && !error && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm font-light text-white">
              <thead className="border-b border-gray-600 font-medium">
                <tr>
                  <th scope="col" className="px-6 py-4">Avatar</th>
                  <th scope="col" className="px-6 py-4">Display Name</th>
                  <th scope="col" className="px-6 py-4">Joined Server</th>
                  <th scope="col" className="px-6 py-4">Actions</th>
                </tr>
              </thead>
              <tbody>
                {newMembers.length > 0 ? (
                  newMembers.map((member) => (
                    <tr key={member.id} className="border-b border-gray-700 hover:bg-gray-700">
                      <td className="px-6 py-4">
                        <img src={member.avatar_url || 'https://cdn.discordapp.com/embed/avatars/0.png'} alt={`${member.display_name}'s avatar`} className="h-10 w-10 rounded-full" />
                      </td>
                      <td className="px-6 py-4 font-medium">{member.display_name}</td>
                      <td className="px-6 py-4">{formatDate(member.joined_at)}</td>
                      <td className="px-6 py-4">
                        <button className="bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-4 rounded mr-2">Graduate</button>
                        <button className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded">View Profile</button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="4" className="text-center py-4">No members are currently in the Welcome Wagon.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </main>
  );
}

export default WelcomeWagon;
