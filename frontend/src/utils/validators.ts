/** Input validation utilities */

export const validateFilename = (filename: string): string | null => {
  if (!filename || filename.trim().length === 0) {
    return 'Filename is required';
  }
  if (filename.length > 255) {
    return 'Filename must be 255 characters or less';
  }
  if (filename.includes('..') || filename.includes('/') || filename.includes('\\')) {
    return 'Filename contains invalid characters';
  }
  return null;
};

export const validateFileSize = (size: number, maxSize: number): string | null => {
  if (size > maxSize) {
    return `File size exceeds maximum allowed size (${formatFileSize(maxSize)})`;
  }
  return null;
};

export const validateJobConfig = (config: {
  task_name?: string;
  max_runtime_minutes?: number;
  max_cost_usd?: number;
  max_documents?: number;
}): Record<string, string> => {
  const errors: Record<string, string> = {};
  
  if (config.task_name && config.task_name.trim().length === 0) {
    errors.task_name = 'Task name cannot be empty';
  }
  
  if (config.max_runtime_minutes !== undefined) {
    if (config.max_runtime_minutes < 1 || config.max_runtime_minutes > 120) {
      errors.max_runtime_minutes = 'Max runtime must be between 1 and 120 minutes';
    }
  }
  
  if (config.max_cost_usd !== undefined) {
    if (config.max_cost_usd < 0 || config.max_cost_usd > 100) {
      errors.max_cost_usd = 'Max cost must be between $0 and $100';
    }
  }
  
  if (config.max_documents !== undefined) {
    if (config.max_documents < 1 || config.max_documents > 10000) {
      errors.max_documents = 'Max documents must be between 1 and 10000';
    }
  }
  
  return errors;
};

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
};
