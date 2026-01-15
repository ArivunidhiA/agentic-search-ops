/** Header component */

import { Menu } from 'lucide-react';

interface HeaderProps {
  onMenuClick: () => void;
}

export const Header = ({ onMenuClick }: HeaderProps) => {
  return (
    <header className="bg-white border-b border-gray-200 h-16 flex items-center px-4 shadow-sm">
      <button
        onClick={onMenuClick}
        className="lg:hidden p-2 rounded-md text-gray-600 hover:bg-gray-100 transition-colors"
        aria-label="Toggle menu"
      >
        <Menu className="w-6 h-6" />
      </button>
      <div className="flex-1 flex items-center justify-between ml-4 lg:ml-0">
        <h1 className="text-xl font-semibold text-gray-900">Claude KB Operator Console</h1>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-600">v0.1.0</span>
        </div>
      </div>
    </header>
  );
};
