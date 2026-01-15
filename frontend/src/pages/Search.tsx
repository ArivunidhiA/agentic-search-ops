/** Search page */

import { useState } from 'react';
import { useQuery } from 'react-query';
import { searchChunks } from '../api/client';
import { SearchBar } from '../components/search/SearchBar';
import { SearchResults } from '../components/search/SearchResults';
import { SearchResult } from '../types';
import { Card } from '../components/ui/card';
import { Search as SearchIcon, Sparkles } from 'lucide-react';

const SAMPLE_QUERIES = [
  'Python programming',
  'database design',
  'web development',
  'cloud computing',
  'artificial intelligence',
];

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

  const handleSampleQuery = (sampleQuery: string) => {
    setQuery(sampleQuery);
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-gray-900">Search</h1>

      <SearchBar onSearch={setQuery} />

      {query ? (
        <SearchResults results={results} isLoading={isLoading} query={query} />
      ) : (
        <Card className="p-8">
          <div className="text-center">
            <div className="flex justify-center mb-4">
              <div className="p-4 bg-yellow-100 rounded-full">
                <SearchIcon className="w-8 h-8 text-yellow-600" />
              </div>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Search Your Knowledge Base</h3>
            <p className="text-gray-500 mb-6">
              Enter a query above to search through your documents and find relevant information.
            </p>
            
            <div className="border-t border-gray-200 pt-6">
              <div className="flex items-center justify-center gap-2 text-sm text-gray-500 mb-4">
                <Sparkles className="w-4 h-4" />
                <span>Try these sample queries:</span>
              </div>
              <div className="flex flex-wrap justify-center gap-2">
                {SAMPLE_QUERIES.map((sampleQuery) => (
                  <button
                    key={sampleQuery}
                    onClick={() => handleSampleQuery(sampleQuery)}
                    className="px-4 py-2 bg-gray-100 hover:bg-yellow-100 text-gray-700 hover:text-yellow-800 rounded-full text-sm transition-colors"
                  >
                    {sampleQuery}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};
