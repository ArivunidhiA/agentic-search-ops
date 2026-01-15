/** Document detail component */

import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Download } from 'lucide-react';
import { useDocument } from '../../hooks/useDocuments';
import { StatusBadge } from '../common/StatusBadge';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { formatFileSize, formatDate } from '../../utils/formatters';

export const DocumentDetail = () => {
  const { id } = useParams<{ id: string }>();
  const { data: document, isLoading, error } = useDocument(id || '');

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error || !document) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-600">
        Failed to load document. Please try again.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link
          to="/documents"
          className="p-2 text-gray-600 hover:text-gray-900 transition-colors"
          aria-label="Back to documents"
        >
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <h1 className="text-2xl font-semibold text-gray-900">{document.filename}</h1>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-1">Status</h3>
            <StatusBadge status={document.status} />
          </div>
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-1">File Size</h3>
            <p className="text-sm text-gray-900">{formatFileSize(document.file_size)}</p>
          </div>
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-1">Content Type</h3>
            <p className="text-sm text-gray-900">{document.content_type}</p>
          </div>
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-1">Upload Date</h3>
            <p className="text-sm text-gray-900">{formatDate(document.upload_timestamp)}</p>
          </div>
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-1">Chunks</h3>
            <p className="text-sm text-gray-900">{document.chunk_count || 0}</p>
          </div>
          {document.download_url && (
            <div>
              <a
                href={document.download_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors"
              >
                <Download className="w-5 h-5" />
                Download
              </a>
            </div>
          )}
        </div>

        {document.metadata && Object.keys(document.metadata).length > 0 && (
          <div className="mt-6 pt-6 border-t border-gray-200">
            <h3 className="text-sm font-medium text-gray-500 mb-2">Metadata</h3>
            <pre className="text-xs bg-gray-50 p-4 rounded-md overflow-x-auto">
              {JSON.stringify(document.metadata, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};
