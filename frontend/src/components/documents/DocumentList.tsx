/** Document list component */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Eye, Download, Trash2 } from 'lucide-react';
import { useDocuments, useDeleteDocument } from '../../hooks/useDocuments';
import { StatusBadge } from '../common/StatusBadge';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { formatFileSize, formatDate } from '../../utils/formatters';
import { Document } from '../../types';
import { ShimmerButton } from '../ui/shimmer-button';
import { Card } from '../ui/card';

export const DocumentList = () => {
  const [skip, setSkip] = useState(0);
  const limit = 50;
  const { data, isLoading, error } = useDocuments(skip, limit);
  const deleteMutation = useDeleteDocument();

  const handleDelete = async (id: string) => {
    if (window.confirm('Are you sure you want to delete this document?')) {
      try {
        await deleteMutation.mutateAsync(id);
      } catch (err) {
        alert('Failed to delete document');
      }
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <Card className="bg-red-50 border border-red-200 text-red-600">
        Failed to load documents. Please try again.
      </Card>
    );
  }

  const documents = data?.documents || [];
  const total = data?.total || 0;

  return (
    <Card showBorderTrail noPadding className="overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">Documents</h2>
        <p className="text-sm text-gray-600 mt-1">Total: {total}</p>
      </div>

      {documents.length === 0 ? (
        <div className="p-8 text-center text-gray-500">
          No documents found. Upload a document to get started.
        </div>
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Filename
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Upload Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Size
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {documents.map((doc: Document) => (
                  <tr key={doc.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{doc.filename}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <StatusBadge status={doc.status} />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(doc.upload_timestamp)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatFileSize(doc.file_size)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex items-center justify-end gap-2">
                        <Link
                          to={`/documents/${doc.id}`}
                          className="p-2 text-yellow-600 hover:text-yellow-800 transition-colors"
                          aria-label="View document"
                        >
                          <Eye className="w-5 h-5" />
                        </Link>
                        {doc.status === 'completed' && (
                          <a
                            href={`/api/v1/documents/${doc.id}/download`}
                            className="p-2 text-gray-600 hover:text-gray-900 transition-colors"
                            aria-label="Download document"
                          >
                            <Download className="w-5 h-5" />
                          </a>
                        )}
                        <button
                          onClick={() => handleDelete(doc.id)}
                          className="p-2 text-red-600 hover:text-red-900 transition-colors"
                          aria-label="Delete document"
                        >
                          <Trash2 className="w-5 h-5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {total > limit && (
            <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
              <ShimmerButton
                onClick={() => setSkip(Math.max(0, skip - limit))}
                disabled={skip === 0}
                variant="secondary"
              >
                Previous
              </ShimmerButton>
              <span className="text-sm text-gray-600">
                Showing {skip + 1} - {Math.min(skip + limit, total)} of {total}
              </span>
              <ShimmerButton
                onClick={() => setSkip(skip + limit)}
                disabled={skip + limit >= total}
                variant="secondary"
              >
                Next
              </ShimmerButton>
            </div>
          )}
        </>
      )}
    </Card>
  );
};
