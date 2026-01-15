/** Job controls component for pause/resume/stop actions */

import { Pause, Play, Square } from 'lucide-react';
import { useControlJob } from '../../hooks/useJobs';
import { JobStatus } from '../../types';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { Card } from '../ui/card';
import { ShimmerButton } from '../ui/shimmer-button';

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
    <Card showBorderTrail>
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Job Controls</h3>
      
      <div className="flex gap-3">
        {status === JobStatus.RUNNING && (
          <ShimmerButton
            onClick={handlePause}
            disabled={isLoading}
            variant="secondary"
          >
            {isLoading ? (
              <LoadingSpinner size="sm" />
            ) : (
              <Pause className="w-5 h-5 mr-2" />
            )}
            Pause
          </ShimmerButton>
        )}
        
        {status === JobStatus.PAUSED && (
          <ShimmerButton
            onClick={handleResume}
            disabled={isLoading}
            variant="primary"
          >
            {isLoading ? (
              <LoadingSpinner size="sm" />
            ) : (
              <Play className="w-5 h-5 mr-2" />
            )}
            Resume
          </ShimmerButton>
        )}
        
        {(status === JobStatus.RUNNING || status === JobStatus.PAUSED) && (
          <ShimmerButton
            onClick={handleStop}
            disabled={isLoading}
            variant="danger"
          >
            {isLoading ? (
              <LoadingSpinner size="sm" />
            ) : (
              <Square className="w-5 h-5 mr-2" />
            )}
            Stop
          </ShimmerButton>
        )}
        
        {status === JobStatus.COMPLETED && (
          <p className="text-sm text-gray-500">Job completed. No actions available.</p>
        )}
        
        {status === JobStatus.FAILED && (
          <p className="text-sm text-gray-500">Job failed. No actions available.</p>
        )}
      </div>
    </Card>
  );
};
