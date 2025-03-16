import React from 'react';
import { NavLink } from 'react-router-dom';
import { Button } from '@/components/ui/button';

const Sidebar: React.FC = () => {
  return (
    <div className="w-64 h-screen bg-gray-100 p-4 flex flex-col gap-2">
      <h2 className="text-2xl font-bold mb-4">Agent Swarm</h2>
      <NavLink to="/" className={({ isActive }) => `w-full ${isActive ? 'bg-gray-200' : ''}`}>
        <Button variant="ghost" className="w-full justify-start">Home</Button>
      </NavLink>
      <NavLink to="/chatrooms" className={({ isActive }) => `w-full ${isActive ? 'bg-gray-200' : ''}`}>
        <Button variant="ghost" className="w-full justify-start">Chatrooms</Button>
      </NavLink>
      <div>
        <NavLink to="/agents" className={({ isActive }) => `w-full ${isActive ? 'bg-gray-200' : ''}`}>
          <Button variant="ghost" className="w-full justify-start">Agents</Button>
        </NavLink>
        <NavLink to="/agents/create" className={({ isActive }) => `w-full pl-4 ${isActive ? 'bg-gray-200' : ''}`}>
          <Button variant="ghost" className="w-full justify-start">Create Agent</Button>
        </NavLink>
      </div>
    </div>
  );
};

export default Sidebar;