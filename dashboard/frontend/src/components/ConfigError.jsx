import React from 'react';
import { ExclamationTriangleIcon } from '@heroicons/react/24/solid';

function ConfigError({ missingKeys }) {
  return (
    <div className="min-h-screen bg-gray-900 flex flex-col items-center justify-center text-white p-4">
      <div className="bg-gray-800 border border-red-500 rounded-lg shadow-lg p-8 max-w-2xl w-full">
        <div className="flex items-center mb-6">
          <ExclamationTriangleIcon className="h-12 w-12 text-red-400 mr-4" />
          <h1 className="text-3xl font-bold text-red-400">Configuration Error</h1>
        </div>
        <p className="text-lg mb-4">The bot failed to start due to missing or invalid configuration. Please resolve the following issues in your <code>config.py</code> or <code>.env</code> file:</p>
        <ul className="list-disc list-inside bg-gray-900 p-4 rounded-md space-y-2">
          {missingKeys.map(key => (
            <li key={key} className="font-mono text-yellow-300">{key}</li>
          ))}
        </ul>
        <p className="mt-6 text-gray-400">After correcting the configuration, please restart the bot.</p>
      </div>
    </div>
  );
}

export default ConfigError;
