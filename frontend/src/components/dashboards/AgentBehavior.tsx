/** Agent behavior dashboard component (per-job metrics) */

import { JobDetail, JobEvent } from '../../types';

interface AgentBehaviorProps {
  job: JobDetail;
  events: JobEvent[];
}

export const AgentBehavior = ({ job, events }: AgentBehaviorProps) => {
  // Calculate metrics from events
  const checkpointCount = events.filter((e) => e.event_type === 'checkpoint').length;
  const errorCount = events.filter((e) => e.event_type === 'error').length;
  const retryCount = events.filter((e) => e.event_type === 'retry').length;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Agent Behavior</h3>
      
      <div className="grid grid-cols-3 gap-4">
        <div>
          <p className="text-sm text-gray-500">Checkpoints</p>
          <p className="text-2xl font-semibold text-gray-900">{checkpointCount}</p>
        </div>
        <div>
          <p className="text-sm text-gray-500">Errors</p>
          <p className="text-2xl font-semibold text-red-600">{errorCount}</p>
        </div>
        <div>
          <p className="text-sm text-gray-500">Retries</p>
          <p className="text-2xl font-semibold text-yellow-600">{retryCount}</p>
        </div>
      </div>
    </div>
  );
};
