/** Job status card component showing key job information */

import { Clock, AlertCircle, CheckCircle, XCircle, Pause } from 'lucide-react';
import { JobDetail } from '../../types';
import { StatusBadge } from '../common/StatusBadge';
import { formatRelativeTime, formatDuration } from '../../utils/formatters';
import { JobStatus } from '../../types';
import { Card } from '../ui/card';

interface JobStatusCardProps {
  job: JobDetail;
}

export const JobStatusCard = ({ job }: JobStatusCardProps) => {
  const getStatusIcon = () => {
    switch (job.status) {
      case JobStatus.RUNNING:
        return <Clock className="w-5 h-5 text-blue-600" />;
      case JobStatus.COMPLETED:
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case JobStatus.FAILED:
        return <XCircle className="w-5 h-5 text-red-600" />;
      case JobStatus.PAUSED:
        return <Pause className="w-5 h-5 text-orange-600" />;
      default:
        return <AlertCircle className="w-5 h-5 text-yellow-600" />;
    }
  };

  const getElapsedTime = () => {
    if (!job.started_at) return null;
    const start = new Date(job.started_at).getTime();
    const end = job.completed_at ? new Date(job.completed_at).getTime() : Date.now();
    return formatDuration((end - start) / 1000);
  };

  return (
    <Card showBorderTrail>
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          {getStatusIcon()}
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Job {job.id.slice(0, 8)}</h2>
            <p className="text-sm text-gray-500">{job.job_type}</p>
          </div>
        </div>
        <StatusBadge status={job.status} />
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
        <div>
          <p className="text-xs text-gray-500 mb-1">Created</p>
          <p className="text-sm text-gray-900">{formatRelativeTime(job.created_at)}</p>
        </div>
        {job.started_at && (
          <div>
            <p className="text-xs text-gray-500 mb-1">Started</p>
            <p className="text-sm text-gray-900">{formatRelativeTime(job.started_at)}</p>
          </div>
        )}
        {getElapsedTime() && (
          <div>
            <p className="text-xs text-gray-500 mb-1">Elapsed</p>
            <p className="text-sm text-gray-900">{getElapsedTime()}</p>
          </div>
        )}
        <div>
          <p className="text-xs text-gray-500 mb-1">Retries</p>
          <p className="text-sm text-gray-900">{job.retry_count} / {job.max_retries}</p>
        </div>
      </div>

      {job.latest_checkpoint && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <p className="text-xs text-gray-500 mb-1">Latest Checkpoint</p>
          <p className="text-sm text-gray-900">{job.latest_checkpoint.step_name}</p>
          <p className="text-xs text-gray-500 mt-1">
            {formatRelativeTime(job.latest_checkpoint.checkpoint_timestamp)}
          </p>
        </div>
      )}

      {job.error_message && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <p className="text-xs text-gray-500 mb-1">Error</p>
          <p className="text-sm text-red-600">{job.error_message}</p>
        </div>
      )}
    </Card>
  );
};
