/** Search bar component */

import { useState } from 'react';
import { Search as SearchIcon } from 'lucide-react';
import { useDebounce } from '../../hooks/useDebounce';
import { Card } from '../ui/card';

interface SearchBarProps {
  onSearch: (query: string) => void;
  placeholder?: string;
}

export const SearchBar = ({ onSearch, placeholder = 'Search documents...' }: SearchBarProps) => {
  const [query, setQuery] = useState('');

  const debouncedSearch = useDebounce((value: string) => {
    if (value.trim()) {
      onSearch(value.trim());
    }
  }, 500);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);
    debouncedSearch(value);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query.trim());
    }
  };

  return (
    <Card showBorderTrail noPadding>
      <form onSubmit={handleSubmit} className="w-full">
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
            <SearchIcon className="h-5 w-5 text-yellow-500" />
          </div>
          <input
            type="text"
            value={query}
            onChange={handleChange}
            placeholder={placeholder}
            className="block w-full pl-12 pr-4 py-3 border-0 rounded-lg leading-5 bg-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:ring-inset"
          />
        </div>
      </form>
    </Card>
  );
};
