/** System health dashboard component */

import { useMetrics } from '../../hooks/useMetrics';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { MetricsCharts } from './MetricsCharts';

export const SystemHealth = () => {
  const { data: metrics, isLoading, error } = useMetrics();

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error || !metrics) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-600">
        Failed to load system health metrics.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">System Overview</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-500">Total Documents</p>
            <p className="text-2xl font-semibold text-gray-900">{metrics.total_documents}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Total Chunks</p>
            <p className="text-2xl font-semibold text-gray-900">{metrics.total_chunks}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Storage Used</p>
            <p className="text-2xl font-semibold text-gray-900">
              {(metrics.storage_used_bytes / 1024 / 1024).toFixed(2)} MB
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">System Health</p>
            <p
              className={`text-2xl font-semibold ${
                metrics.system_health === 'healthy' ? 'text-green-600' : 'text-orange-600'
              }`}
            >
              {metrics.system_health}
            </p>
          </div>
        </div>
      </div>

      <MetricsCharts metrics={metrics} />
    </div>
  );
};
