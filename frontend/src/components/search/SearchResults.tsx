/** Search results component */

import { Link } from 'react-router-dom';
import { SearchResult } from '../../types';
import { formatFileSize, formatDate } from '../../utils/formatters';
import { LoadingSpinner } from '../common/LoadingSpinner';

interface SearchResultsProps {
  results: SearchResult[];
  isLoading: boolean;
  query: string;
}

export const SearchResults = ({ results, isLoading, query }: SearchResultsProps) => {
  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-8 text-center">
        <p className="text-gray-500">No results found for "{query}"</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="bg-white rounded-lg shadow p-4">
        <p className="text-sm text-gray-600">
          Found {results.length} result{results.length !== 1 ? 's' : ''} for "{query}"
        </p>
      </div>

      {results.map((result) => (
        <div key={result.chunk_id} className="bg-white rounded-lg shadow p-6">
          <div className="flex items-start justify-between mb-3">
            <div>
              <Link
                to={`/documents/${result.document_id}`}
                className="text-sm font-medium text-primary-600 hover:text-primary-800"
              >
                {result.document_metadata.filename}
              </Link>
              <p className="text-xs text-gray-500 mt-1">
                Chunk {result.chunk_index} • Score: {result.score}
              </p>
            </div>
            <div className="text-xs text-gray-500">
              {formatFileSize(result.document_metadata.file_size)}
            </div>
          </div>
          
          <div
            className="text-sm text-gray-700 mt-3 line-clamp-3"
            dangerouslySetInnerHTML={{ __html: result.highlighted_content }}
          />
        </div>
      ))}
    </div>
  );
};
