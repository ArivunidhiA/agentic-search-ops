/** Dashboard page */

import { Link } from 'react-router-dom';
import { Plus, Search, Briefcase } from 'lucide-react';
import { SystemHealth } from '../components/dashboards/SystemHealth';
import { useJobs } from '../hooks/useJobs';
import { useDocuments } from '../hooks/useDocuments';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { JobStatus } from '../types';

export const Dashboard = () => {
  const { data: jobsData, isLoading: jobsLoading } = useJobs(0, 10);
  const { data: documentsData, isLoading: documentsLoading } = useDocuments(0, 5);

  const activeJobs = jobsData?.jobs?.filter((job) => job.status === JobStatus.RUNNING) || [];
  const recentJobs = jobsData?.jobs?.slice(0, 5) || [];
  const recentDocuments = documentsData?.documents?.slice(0, 5) || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>
        <div className="flex gap-3">
          <Link
            to="/jobs"
            className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors"
          >
            <Plus className="w-5 h-5" />
            New Job
          </Link>
          <Link
            to="/search"
            className="flex items-center gap-2 px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
          >
            <Search className="w-5 h-5" />
            Search
          </Link>
        </div>
      </div>

      <SystemHealth />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Active Jobs</h2>
            <Link
              to="/jobs"
              className="text-sm text-primary-600 hover:text-primary-800"
            >
              View all
            </Link>
          </div>
          {jobsLoading ? (
            <LoadingSpinner />
          ) : activeJobs.length === 0 ? (
            <p className="text-sm text-gray-500">No active jobs</p>
          ) : (
            <div className="space-y-2">
              {activeJobs.map((job) => (
                <Link
                  key={job.id}
                  to={`/jobs/${job.id}`}
                  className="block p-3 rounded-md hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-900">{job.job_type}</span>
                    <span className="text-xs text-gray-500">{job.id.slice(0, 8)}</span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Recent Documents</h2>
            <Link
              to="/documents"
              className="text-sm text-primary-600 hover:text-primary-800"
            >
              View all
            </Link>
          </div>
          {documentsLoading ? (
            <LoadingSpinner />
          ) : recentDocuments.length === 0 ? (
            <p className="text-sm text-gray-500">No documents yet</p>
          ) : (
            <div className="space-y-2">
              {recentDocuments.map((doc) => (
                <Link
                  key={doc.id}
                  to={`/documents/${doc.id}`}
                  className="block p-3 rounded-md hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-900 truncate">{doc.filename}</span>
                    <span className="text-xs text-gray-500">
                      {new Date(doc.upload_timestamp).toLocaleDateString()}
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
