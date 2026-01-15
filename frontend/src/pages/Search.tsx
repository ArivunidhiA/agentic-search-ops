/** Search page */

import { useState } from 'react';
import { useQuery } from 'react-query';
import { searchChunks } from '../api/client';
import { SearchBar } from '../components/search/SearchBar';
import { SearchResults } from '../components/search/SearchResults';
import { SearchResult } from '../types';

export const Search = () => {
  const [query, setQuery] = useState('');

  const { data, isLoading } = useQuery<{ results: SearchResult[] }>(
    ['search', query],
    () => searchChunks(query, 10),
    {
      enabled: query.length > 0,
      staleTime: 30000,
    }
  );

  const results = data?.results || [];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-gray-900">Search</h1>

      <SearchBar onSearch={setQuery} />

      {query && <SearchResults results={results} isLoading={isLoading} query={query} />}
    </div>
  );
};
