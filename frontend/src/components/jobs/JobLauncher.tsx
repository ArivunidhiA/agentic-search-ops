/** Job launcher component with guardrails */

import { useState } from 'react';
import { Play, Save } from 'lucide-react';
import { useCreateJob } from '../../hooks/useJobs';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { validateJobConfig } from '../../utils/validators';
import { JobType } from '../../types';
import { useNavigate } from 'react-router-dom';
import { Card } from '../ui/card';
import { ShimmerButton } from '../ui/shimmer-button';

export const JobLauncher = () => {
  const navigate = useNavigate();
  const createJobMutation = useCreateJob();
  const [errors, setErrors] = useState<Record<string, string>>({});
  
  const [formData, setFormData] = useState({
    task_name: '',
    job_type: JobType.INGESTION,
    data_source: '',
    max_runtime_minutes: 60,
    max_cost_usd: 5.0,
    max_documents: 100,
    execution_mode: 'conservative' as 'conservative' | 'aggressive',
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: name === 'max_runtime_minutes' || name === 'max_cost_usd' || name === 'max_documents'
        ? parseFloat(value) || 0
        : value,
    }));
    // Clear error for this field
    if (errors[name]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate
    const validationErrors = validateJobConfig(formData);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    try {
      const job = await createJobMutation.mutateAsync({
        job_type: formData.job_type,
        config: {
          task_name: formData.task_name,
          data_source: formData.data_source,
          max_runtime_minutes: formData.max_runtime_minutes,
          max_cost_usd: formData.max_cost_usd,
          max_documents: formData.max_documents,
          execution_mode: formData.execution_mode,
        },
      });
      navigate(`/jobs/${job.id}`);
    } catch (err) {
      alert('Failed to create job. Please try again.');
    }
  };

  const handleDryRun = () => {
    const validationErrors = validateJobConfig(formData);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      alert('Validation failed. Please fix the errors.');
    } else {
      alert('Validation passed! Job configuration is valid.');
    }
  };

  const handleSaveTemplate = () => {
    const templates = JSON.parse(localStorage.getItem('jobTemplates') || '[]');
    templates.push({
      ...formData,
      name: formData.task_name || 'Untitled Template',
      saved_at: new Date().toISOString(),
    });
    localStorage.setItem('jobTemplates', JSON.stringify(templates));
    alert('Template saved!');
  };

  return (
    <Card showBorderTrail>
      <h2 className="text-xl font-semibold text-gray-900 mb-6">Launch New Job</h2>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label htmlFor="task_name" className="block text-sm font-medium text-gray-700 mb-2">
            Task Name <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            id="task_name"
            name="task_name"
            value={formData.task_name}
            onChange={handleChange}
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
          {errors.task_name && (
            <p className="mt-1 text-sm text-red-600">{errors.task_name}</p>
          )}
        </div>

        <div>
          <label htmlFor="job_type" className="block text-sm font-medium text-gray-700 mb-2">
            Job Type <span className="text-red-500">*</span>
          </label>
          <select
            id="job_type"
            name="job_type"
            value={formData.job_type}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value={JobType.INGESTION}>Knowledge Ingestion</option>
            <option value={JobType.SEARCH}>Deep Search</option>
            <option value={JobType.SYNTHESIS}>Synthesis</option>
            <option value={JobType.REFRESH}>Refresh</option>
          </select>
        </div>

        <div>
          <label htmlFor="data_source" className="block text-sm font-medium text-gray-700 mb-2">
            Data Source
          </label>
          <input
            type="text"
            id="data_source"
            name="data_source"
            value={formData.data_source}
            onChange={handleChange}
            placeholder="File path, S3 path, or URL list"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label htmlFor="max_runtime_minutes" className="block text-sm font-medium text-gray-700 mb-2">
              Max Runtime (minutes)
            </label>
            <input
              type="number"
              id="max_runtime_minutes"
              name="max_runtime_minutes"
              value={formData.max_runtime_minutes}
              onChange={handleChange}
              min="1"
              max="120"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
            {errors.max_runtime_minutes && (
              <p className="mt-1 text-sm text-red-600">{errors.max_runtime_minutes}</p>
            )}
          </div>

          <div>
            <label htmlFor="max_cost_usd" className="block text-sm font-medium text-gray-700 mb-2">
              Max Cost (USD)
            </label>
            <input
              type="number"
              id="max_cost_usd"
              name="max_cost_usd"
              value={formData.max_cost_usd}
              onChange={handleChange}
              min="0"
              max="100"
              step="0.1"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
            {errors.max_cost_usd && (
              <p className="mt-1 text-sm text-red-600">{errors.max_cost_usd}</p>
            )}
          </div>

          <div>
            <label htmlFor="max_documents" className="block text-sm font-medium text-gray-700 mb-2">
              Max Documents
            </label>
            <input
              type="number"
              id="max_documents"
              name="max_documents"
              value={formData.max_documents}
              onChange={handleChange}
              min="1"
              max="10000"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
            {errors.max_documents && (
              <p className="mt-1 text-sm text-red-600">{errors.max_documents}</p>
            )}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Execution Mode
          </label>
          <div className="flex gap-4">
            <label className="flex items-center">
              <input
                type="radio"
                name="execution_mode"
                value="conservative"
                checked={formData.execution_mode === 'conservative'}
                onChange={handleChange}
                className="mr-2"
              />
              Conservative
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                name="execution_mode"
                value="aggressive"
                checked={formData.execution_mode === 'aggressive'}
                onChange={handleChange}
                className="mr-2"
              />
              Aggressive
            </label>
          </div>
        </div>

        <div className="flex gap-4 pt-4">
          <ShimmerButton
            type="submit"
            disabled={createJobMutation.isLoading}
            variant="primary"
          >
            {createJobMutation.isLoading ? (
              <>
                <LoadingSpinner size="sm" />
                <span className="ml-2">Starting...</span>
              </>
            ) : (
              <>
                <Play className="w-5 h-5 mr-2" />
                Start Job
              </>
            )}
          </ShimmerButton>
          <ShimmerButton
            type="button"
            onClick={handleDryRun}
            variant="secondary"
          >
            Dry Run
          </ShimmerButton>
          <ShimmerButton
            type="button"
            onClick={handleSaveTemplate}
            variant="secondary"
          >
            <Save className="w-5 h-5 mr-2" />
            Save as Template
          </ShimmerButton>
        </div>
      </form>
    </Card>
  );
};
