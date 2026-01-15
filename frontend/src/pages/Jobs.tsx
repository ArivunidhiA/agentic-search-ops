/** Jobs page */

import { Link } from 'react-router-dom';
import { Plus } from 'lucide-react';
import { useJobs } from '../hooks/useJobs';
import { JobLauncher } from '../components/jobs/JobLauncher';
import { StatusBadge } from '../components/common/StatusBadge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { formatDate } from '../utils/formatters';
import { useState } from 'react';
import { ShimmerButton } from '../components/ui/shimmer-button';
import { Card } from '../components/ui/card';

export const Jobs = () => {
  const [showLauncher, setShowLauncher] = useState(false);
  const { data, isLoading, error } = useJobs(0, 50);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <Card className="bg-red-50 border border-red-200 text-red-600">
        Failed to load jobs. Please try again.
      </Card>
    );
  }

  const jobs = data?.jobs || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-gray-900">Jobs</h1>
        <ShimmerButton
          onClick={() => setShowLauncher(!showLauncher)}
          className="flex items-center gap-2"
        >
          <Plus className="w-5 h-5" />
          {showLauncher ? 'Hide' : 'New Job'}
        </ShimmerButton>
      </div>

      {showLauncher && <JobLauncher />}

      <Card showBorderTrail noPadding className="overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Job List</h2>
        </div>

        {jobs.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            No jobs found. Create a new job to get started.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Job Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {jobs.map((job) => (
                  <tr key={job.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{job.job_type}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <StatusBadge status={job.status} />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(job.created_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <Link
                        to={`/jobs/${job.id}`}
                        className="text-primary-600 hover:text-primary-900"
                      >
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
};
