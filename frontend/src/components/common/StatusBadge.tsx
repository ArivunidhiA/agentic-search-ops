/** Status badge component for displaying status with color coding */

import { DocumentStatus, JobStatus } from '../../types';
import clsx from 'clsx';

interface StatusBadgeProps {
  status: DocumentStatus | JobStatus | string;
  className?: string;
}

export const StatusBadge = ({ status, className }: StatusBadgeProps) => {
  const statusColors: Record<string, string> = {
    // Document statuses
    pending: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    processing: 'bg-blue-100 text-blue-800 border-blue-200',
    completed: 'bg-green-100 text-green-800 border-green-200',
    failed: 'bg-red-100 text-red-800 border-red-200',
    // Job statuses
    running: 'bg-blue-100 text-blue-800 border-blue-200',
    paused: 'bg-orange-100 text-orange-800 border-orange-200',
  };

  const colorClass = statusColors[status.toLowerCase()] || 'bg-gray-100 text-gray-800 border-gray-200';

  return (
    <span
      className={clsx(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border',
        colorClass,
        className
      )}
    >
      {status}
    </span>
  );
};
