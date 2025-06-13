import React from 'react';
import { NavLink } from 'react-router-dom';
import { CogIcon, UsersIcon, ChartBarIcon, ShieldCheckIcon } from '@heroicons/react/24/outline';

const navigation = [
  { name: 'Dashboard', href: '/', icon: ChartBarIcon },
  { name: 'Welcome Wagon', href: '/welcome-wagon', icon: UsersIcon },
  { name: 'SAM Reports', href: '/sam-reports', icon: ShieldCheckIcon },
  { name: 'Configuration', href: '/configuration', icon: CogIcon },
];

function classNames(...classes) {
  return classes.filter(Boolean).join(' ');
}

function Sidebar() {
  return (
    <div className="flex flex-col h-full bg-gray-900 text-gray-300 w-64 p-4">
      <div className="flex items-center mb-8">
        <h1 className="text-xl font-bold text-white">WLM Network</h1>
      </div>
      <nav className="flex-1">
        <ul role="list" className="space-y-2">
          {navigation.map((item) => (
            <li key={item.name}>
              <NavLink
                to={item.href}
                className={({ isActive }) =>
                  classNames(
                    isActive
                      ? 'bg-gray-800 text-white'
                      : 'text-gray-400 hover:text-white hover:bg-gray-800',
                    'group flex gap-x-3 rounded-md p-2 text-sm leading-6 font-semibold'
                  )
                }
              >
                <item.icon className="h-6 w-6 shrink-0" aria-hidden="true" />
                {item.name}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  );
}

export default Sidebar;

