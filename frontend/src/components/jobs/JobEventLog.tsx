/** Job event log component showing timestamped events */

import { JobEvent, JobEventType } from '../../types';
import { formatDate } from '../../utils/formatters';
import { Clock, CheckCircle, XCircle, AlertCircle, RotateCcw, Pause, Play } from 'lucide-react';
import { Card } from '../ui/card';

interface JobEventLogProps {
  events: JobEvent[];
}

const getEventIcon = (eventType: JobEventType) => {
  switch (eventType) {
    case JobEventType.START:
      return <Play className="w-4 h-4 text-blue-600" />;
    case JobEventType.CHECKPOINT:
      return <Clock className="w-4 h-4 text-yellow-600" />;
    case JobEventType.COMPLETE:
      return <CheckCircle className="w-4 h-4 text-green-600" />;
    case JobEventType.ERROR:
      return <XCircle className="w-4 h-4 text-red-600" />;
    case JobEventType.RETRY:
      return <RotateCcw className="w-4 h-4 text-yellow-600" />;
    case JobEventType.PAUSE:
      return <Pause className="w-4 h-4 text-orange-600" />;
    case JobEventType.RESUME:
      return <Play className="w-4 h-4 text-blue-600" />;
    default:
      return <AlertCircle className="w-4 h-4 text-gray-600" />;
  }
};

export const JobEventLog = ({ events }: JobEventLogProps) => {
  return (
    <Card showBorderTrail>
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Event Log</h3>
      
      {events.length === 0 ? (
        <p className="text-sm text-gray-500">No events yet.</p>
      ) : (
        <div className="space-y-3">
          {events.map((event) => (
            <div
              key={event.id}
              className="flex items-start gap-3 p-3 rounded-md hover:bg-gray-50 transition-colors"
            >
              <div className="mt-0.5">{getEventIcon(event.event_type)}</div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-gray-900">
                    {event.event_type}
                  </span>
                  <span className="text-xs text-gray-500">
                    {formatDate(event.timestamp)}
                  </span>
                </div>
                {event.event_data && Object.keys(event.event_data).length > 0 && (
                  <div className="mt-1 text-xs text-gray-600">
                    <pre className="whitespace-pre-wrap">
                      {JSON.stringify(event.event_data, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
};
