/** Job controls component for pause/resume/stop actions */

import { Pause, Play, Square } from 'lucide-react';
import { useControlJob } from '../../hooks/useJobs';
import { JobStatus } from '../../types';
import { LoadingSpinner } from '../common/LoadingSpinner';

interface JobControlsProps {
  jobId: string;
  status: JobStatus;
}

export const JobControls = ({ jobId, status }: JobControlsProps) => {
  const controlMutation = useControlJob();

  const handlePause = async () => {
    if (window.confirm('Pause this job at the next checkpoint?')) {
      try {
        await controlMutation.mutateAsync({ jobId, action: 'pause' });
      } catch (err) {
        alert('Failed to pause job');
      }
    }
  };

  const handleResume = async () => {
    try {
      await controlMutation.mutateAsync({ jobId, action: 'resume' });
    } catch (err) {
      alert('Failed to resume job');
    }
  };

  const handleStop = async () => {
    if (window.confirm('Stop this job? This action cannot be undone.')) {
      try {
        await controlMutation.mutateAsync({ jobId, action: 'stop' });
      } catch (err) {
        alert('Failed to stop job');
      }
    }
  };

  const isLoading = controlMutation.isLoading;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Job Controls</h3>
      
      <div className="flex gap-3">
        {status === JobStatus.RUNNING && (
          <button
            onClick={handlePause}
            disabled={isLoading}
            className="flex items-center gap-2 px-4 py-2 bg-orange-600 text-white rounded-md hover:bg-orange-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? (
              <LoadingSpinner size="sm" />
            ) : (
              <Pause className="w-5 h-5" />
            )}
            Pause
          </button>
        )}
        
        {status === JobStatus.PAUSED && (
          <button
            onClick={handleResume}
            disabled={isLoading}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? (
              <LoadingSpinner size="sm" />
            ) : (
              <Play className="w-5 h-5" />
            )}
            Resume
          </button>
        )}
        
        {(status === JobStatus.RUNNING || status === JobStatus.PAUSED) && (
          <button
            onClick={handleStop}
            disabled={isLoading}
            className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? (
              <LoadingSpinner size="sm" />
            ) : (
              <Square className="w-5 h-5" />
            )}
            Stop
          </button>
        )}
        
        {status === JobStatus.COMPLETED && (
          <p className="text-sm text-gray-500">Job completed. No actions available.</p>
        )}
        
        {status === JobStatus.FAILED && (
          <p className="text-sm text-gray-500">Job failed. No actions available.</p>
        )}
      </div>
    </div>
  );
};
