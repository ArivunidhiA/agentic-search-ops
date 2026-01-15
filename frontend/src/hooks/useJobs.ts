/** Custom hooks for job data fetching */

import { useQuery, useMutation, useQueryClient } from 'react-query';
import {
  getJobs,
  getJob,
  getJobEvents,
  createJob,
  controlJob,
} from '../api/client';
import type { Job, JobDetail, JobEvent, JobConfig } from '../types';
import { JobStatus } from '../types';

export const useJobs = (skip: number = 0, limit: number = 50, status?: string) => {
  return useQuery(
    ['jobs', skip, limit, status],
    () => getJobs(skip, limit, status),
    {
      staleTime: 30000,
      refetchInterval: (data) => {
        // Auto-refresh if any job is running
        const jobs = data?.jobs || [];
        const hasRunning = jobs.some((job: Job) => job.status === JobStatus.RUNNING);
        return hasRunning ? 2000 : false;
      },
    }
  );
};

export const useJob = (id: string) => {
  return useQuery(
    ['job', id],
    () => getJob(id),
    {
      staleTime: 5000,
      refetchInterval: (data) => {
        // Poll every 2 seconds if job is running
        return data?.status === JobStatus.RUNNING ? 2000 : false;
      },
    }
  );
};

export const useJobEvents = (jobId: string, skip: number = 0, limit: number = 100) => {
  return useQuery(
    ['job-events', jobId, skip, limit],
    () => getJobEvents(jobId, skip, limit),
    {
      staleTime: 5000,
      refetchInterval: (data) => {
        // Poll every 5 seconds if job is running
        const job = data?.job_id;
        // We need to check job status, but we don't have it here
        // For now, always poll if we have events
        return data?.events && data.events.length > 0 ? 5000 : false;
      },
    }
  );
};

export const useCreateJob = () => {
  const queryClient = useQueryClient();
  
  return useMutation(createJob, {
    onSuccess: () => {
      queryClient.invalidateQueries('jobs');
    },
  });
};

export const useControlJob = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    ({ jobId, action }: { jobId: string; action: 'pause' | 'resume' | 'stop' }) =>
      controlJob(jobId, action),
    {
      onSuccess: (data) => {
        queryClient.invalidateQueries(['job', data.id]);
        queryClient.invalidateQueries('jobs');
      },
    }
  );
};
