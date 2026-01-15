/** Search results component */

import { Link } from 'react-router-dom';
import { SearchResult } from '../../types';
import { formatFileSize } from '../../utils/formatters';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { Card } from '../ui/card';

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
      <Card className="text-center">
        <p className="text-gray-500">No results found for "{query}"</p>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <Card>
        <p className="text-sm text-gray-600">
          Found {results.length} result{results.length !== 1 ? 's' : ''} for "{query}"
        </p>
      </Card>

      {results.map((result) => (
        <Card key={result.chunk_id} showBorderTrail>
          <div className="flex items-start justify-between mb-3">
            <div>
              <Link
                to={`/documents/${result.document_id}`}
                className="text-sm font-medium text-yellow-600 hover:text-yellow-800"
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
        </Card>
      ))}
    </div>
  );
};
