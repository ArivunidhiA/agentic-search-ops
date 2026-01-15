/** API client using axios */

import axios, { type AxiosError, type AxiosInstance } from 'axios';
import type {
  Document,
  DocumentDetail,
  Job,
  JobDetail,
  JobConfig,
  JobEvent,
  SearchRequest,
  SearchResponse,
  Metrics,
  PaginatedResponse,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    if (import.meta.env.DEV) {
      console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
    }
    return config;
  },
  (error) => {
    if (import.meta.env.DEV) {
      console.error('[API] Request error:', error);
    }
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    if (import.meta.env.DEV) {
      console.log(`[API] Response:`, response.status, response.data);
    }
    return response;
  },
  (error: AxiosError) => {
    if (import.meta.env.DEV) {
      console.error('[API] Response error:', error.response?.status, error.response?.data);
    }
    return Promise.reject(error);
  }
);

// Document endpoints
export const uploadDocument = async (file: File): Promise<Document> => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await apiClient.post<Document>('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const getDocuments = async (
  skip: number = 0,
  limit: number = 50,
  status?: string
): Promise<PaginatedResponse<Document>> => {
  const params: Record<string, string | number> = { skip, limit };
  if (status) params.status = status;
  
  const response = await apiClient.get<PaginatedResponse<Document>>('/documents', { params });
  return response.data;
};

export const getDocument = async (id: string): Promise<DocumentDetail> => {
  const response = await apiClient.get<DocumentDetail>(`/documents/${id}`);
  return response.data;
};

export const deleteDocument = async (id: string): Promise<void> => {
  await apiClient.delete(`/documents/${id}`);
};

// Search endpoints
export const searchChunks = async (
  query: string,
  limit: number = 10,
  documentIds?: string[]
): Promise<SearchResponse> => {
  const request: SearchRequest = { query, limit, document_ids: documentIds };
  const response = await apiClient.post<SearchResponse>('/search', request);
  return response.data;
};

// Job endpoints
export const createJob = async (config: JobConfig): Promise<Job> => {
  const response = await apiClient.post<Job>('/jobs', config);
  return response.data;
};

export const getJobs = async (
  skip: number = 0,
  limit: number = 50,
  status?: string
): Promise<PaginatedResponse<Job>> => {
  const params: Record<string, string | number> = { skip, limit };
  if (status) params.status = status;
  
  const response = await apiClient.get<PaginatedResponse<Job>>('/jobs', { params });
  return response.data;
};

export const getJob = async (id: string): Promise<JobDetail> => {
  const response = await apiClient.get<JobDetail>(`/jobs/${id}`);
  return response.data;
};

export const getJobEvents = async (
  jobId: string,
  skip: number = 0,
  limit: number = 100
): Promise<PaginatedResponse<JobEvent>> => {
  const params = { skip, limit };
  const response = await apiClient.get<PaginatedResponse<JobEvent>>(
    `/jobs/${jobId}/events`,
    { params }
  );
  return response.data;
};

export const controlJob = async (
  jobId: string,
  action: 'pause' | 'resume' | 'stop'
): Promise<Job> => {
  const response = await apiClient.post<Job>(`/jobs/${jobId}/control`, { action });
  return response.data;
};

export const createCheckpoint = async (
  jobId: string,
  stateData: Record<string, unknown>,
  stepName: string
): Promise<{ checkpoint_id: string; timestamp: string }> => {
  const response = await apiClient.post(`/jobs/${jobId}/checkpoint`, {
    state_data: stateData,
    step_name: stepName,
  });
  return response.data;
};

// Metrics endpoint
export const getMetrics = async (): Promise<Metrics> => {
  const response = await apiClient.get<Metrics>('/metrics');
  return response.data;
};

// Health check
export const healthCheck = async (): Promise<{ status: string; timestamp: string }> => {
  const response = await apiClient.get('/health');
  return response.data;
};
