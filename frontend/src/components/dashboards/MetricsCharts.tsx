/** Metrics charts component using Recharts */

import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { Metrics } from '../../types';

interface MetricsChartsProps {
  metrics: Metrics;
}

export const MetricsCharts = ({ metrics }: MetricsChartsProps) => {
  // Prepare data for charts
  const jobsByStatusData = Object.entries(metrics.jobs_by_status).map(([status, count]) => ({
    status,
    count,
  }));

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h4 className="text-md font-semibold text-gray-900 mb-4">Jobs by Status</h4>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={jobsByStatusData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="status" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="count" fill="#0ea5e9" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h4 className="text-md font-semibold text-gray-900 mb-4">Recent Activity</h4>
        <div className="space-y-2">
          {metrics.recent_activity.slice(0, 10).map((activity) => (
            <div key={activity.id} className="flex items-center justify-between text-sm">
              <span className="text-gray-600">{activity.event_type}</span>
              <span className="text-gray-400 text-xs">
                {new Date(activity.timestamp).toLocaleTimeString()}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
