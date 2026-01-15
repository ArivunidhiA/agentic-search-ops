/** Documents page */

import { DocumentUpload } from '../components/documents/DocumentUpload';
import { DocumentList } from '../components/documents/DocumentList';

export const Documents = () => {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-gray-900">Documents</h1>
      </div>

      <DocumentUpload />
      <DocumentList />
    </div>
  );
};
