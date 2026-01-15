/** Job timeline component showing job progress visually */

import { JobDetail, JobEvent, JobEventType } from '../../types';
import clsx from 'clsx';
import { Card } from '../ui/card';

interface JobTimelineProps {
  job: JobDetail;
  events: JobEvent[];
}

const stepOrder = ['PLANNING', 'EXECUTING', 'VERIFYING', 'SYNTHESIZING'];

export const JobTimeline = ({ events }: JobTimelineProps) => {
  // Extract step information from events
  const stepStatuses = stepOrder.map((step) => {
    const stepEvents = events.filter((e) => {
      const stepName = e.event_data?.step_name as string | undefined;
      return (stepName?.toUpperCase().includes(step)) ||
        e.event_type === JobEventType.CHECKPOINT;
    });
    const isComplete = stepEvents.some((e) => e.event_type === JobEventType.COMPLETE);
    const isActive = stepEvents.some((e) => 
      e.event_type === JobEventType.CHECKPOINT && 
      events.indexOf(e) === events.length - 1
    );
    return { name: step, isComplete, isActive, events: stepEvents };
  });

  return (
    <Card showBorderTrail>
      <h3 className="text-lg font-semibold text-gray-900 mb-6">Timeline</h3>
      
      <div className="space-y-4">
        {stepStatuses.map((step, index) => (
          <div key={step.name} className="flex items-start gap-4">
            <div className="flex flex-col items-center">
              <div
                className={clsx(
                  'w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium',
                  step.isComplete
                    ? 'bg-green-100 text-green-800'
                    : step.isActive
                    ? 'bg-yellow-100 text-yellow-800'
                    : 'bg-gray-100 text-gray-400'
                )}
              >
                {index + 1}
              </div>
              {index < stepStatuses.length - 1 && (
                <div
                  className={clsx(
                    'w-0.5 h-16 mt-2',
                    step.isComplete ? 'bg-green-200' : 'bg-gray-200'
                  )}
                />
              )}
            </div>
            <div className="flex-1 pb-8">
              <h4 className="font-medium text-gray-900">{step.name}</h4>
              {step.events.length > 0 && (
                <p className="text-sm text-gray-500 mt-1">
                  {step.events.length} checkpoint{step.events.length !== 1 ? 's' : ''}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
};
