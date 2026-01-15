/** Job detail page - THE MOST IMPORTANT SCREEN */

import { useParams } from 'react-router-dom';
import { useJob, useJobEvents } from '../hooks/useJobs';
import { JobStatusCard } from '../components/jobs/JobStatusCard';
import { JobTimeline } from '../components/jobs/JobTimeline';
import { JobEventLog } from '../components/jobs/JobEventLog';
import { JobControls } from '../components/jobs/JobControls';
import { OperatorChat } from '../components/operator/OperatorChat';
import { AgentBehavior } from '../components/dashboards/AgentBehavior';
import { LoadingSpinner } from '../components/common/LoadingSpinner';

export const JobDetail = () => {
  const { id } = useParams<{ id: string }>();
  const { data: job, isLoading: jobLoading } = useJob(id || '');
  const { data: eventsData, isLoading: eventsLoading } = useJobEvents(id || '', 0, 100);

  if (jobLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!job) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-600">
        Job not found.
      </div>
    );
  }

  const events = eventsData?.events || [];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-gray-900">Job Details</h1>

      <JobStatusCard job={job} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <JobTimeline job={job} events={events} />
        <JobControls jobId={job.id} status={job.status} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <JobEventLog events={events} />
        <AgentBehavior job={job} events={events} />
      </div>

      <OperatorChat jobId={job.id} />
    </div>
  );
};
