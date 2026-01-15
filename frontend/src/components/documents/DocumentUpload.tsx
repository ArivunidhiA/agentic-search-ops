/** Document upload component */

import { useState, useRef } from 'react';
import { Upload, X, AlertCircle } from 'lucide-react';
import { useUploadDocument } from '../../hooks/useDocuments';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { validateFilename, validateFileSize } from '../../utils/validators';
import { Card } from '../ui/card';
import { ShimmerButton } from '../ui/shimmer-button';

interface DocumentUploadProps {
  onSuccess?: () => void;
}

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

export const DocumentUpload = ({ onSuccess }: DocumentUploadProps) => {
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const uploadMutation = useUploadDocument();

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    setError(null);

    // Validate filename
    const filenameError = validateFilename(selectedFile.name);
    if (filenameError) {
      setError(filenameError);
      return;
    }

    // Validate file size
    const sizeError = validateFileSize(selectedFile.size, MAX_FILE_SIZE);
    if (sizeError) {
      setError(sizeError);
      return;
    }

    setFile(selectedFile);
  };

  const handleUpload = async () => {
    if (!file) return;

    setError(null);
    try {
      await uploadMutation.mutateAsync(file);
      setFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      onSuccess?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    }
  };

  const handleRemove = () => {
    setFile(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <Card showBorderTrail>
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Upload Document</h3>
      
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select File
          </label>
          <div className="flex items-center gap-4">
            <input
              ref={fileInputRef}
              type="file"
              onChange={handleFileSelect}
              className="hidden"
              id="file-upload"
              accept=".pdf,.txt,.md,.docx"
            />
            <ShimmerButton
              type="button"
              onClick={() => fileInputRef.current?.click()}
              variant="primary"
            >
              <Upload className="w-5 h-5 mr-2" />
              Choose File
            </ShimmerButton>
            {file && (
              <div className="flex items-center gap-2 text-sm text-gray-700">
                <span>{file.name}</span>
                <button
                  onClick={handleRemove}
                  className="p-1 text-gray-500 hover:text-red-600 transition-colors"
                  aria-label="Remove file"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>
        </div>

        {error && (
          <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 p-3 rounded-md">
            <AlertCircle className="w-5 h-5" />
            <span>{error}</span>
          </div>
        )}

        <ShimmerButton
          onClick={handleUpload}
          disabled={!file || uploadMutation.isLoading}
          variant="primary"
          className="w-full"
        >
          {uploadMutation.isLoading ? (
            <>
              <LoadingSpinner size="sm" />
              <span className="ml-2">Uploading...</span>
            </>
          ) : (
            'Upload Document'
          )}
        </ShimmerButton>
      </div>
    </Card>
  );
};
