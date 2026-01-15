/** TypeScript types matching backend Pydantic models */

export enum DocumentStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

export enum JobType {
  INGESTION = 'ingestion',
  SEARCH = 'search',
  SYNTHESIS = 'synthesis',
  REFRESH = 'refresh',
}

export enum JobStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  PAUSED = 'paused',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

export enum JobEventType {
  START = 'start',
  CHECKPOINT = 'checkpoint',
  ERROR = 'error',
  RETRY = 'retry',
  COMPLETE = 'complete',
  PAUSE = 'pause',
  RESUME = 'resume',
}

export interface Document {
  id: string;
  filename: string;
  s3_key: string;
  upload_timestamp: string;
  file_size: number;
  content_type: string;
  status: DocumentStatus;
  metadata: Record<string, unknown>;
  created_by?: string;
}

export interface Chunk {
  id: string;
  document_id: string;
  content: string;
  chunk_index: number;
  token_count?: number;
  embedding?: string;
  created_at: string;
}

export interface Job {
  id: string;
  job_type: JobType;
  status: JobStatus;
  config: Record<string, unknown>;
  result: Record<string, unknown>;
  error_message?: string;
  created_at: string;
  updated_at: string;
  started_at?: string;
  completed_at?: string;
  retry_count: number;
  max_retries: number;
}

export interface JobState {
  id: string;
  job_id: string;
  state_data: Record<string, unknown>;
  checkpoint_timestamp: string;
  step_name: string;
}

export interface JobEvent {
  id: string;
  job_id: string;
  event_type: JobEventType;
  event_data: Record<string, unknown>;
  timestamp: string;
}

export interface JobConfig {
  job_type: JobType;
  config: {
    task_name?: string;
    data_source?: string;
    max_runtime_minutes?: number;
    max_cost_usd?: number;
    max_documents?: number;
    execution_mode?: 'conservative' | 'aggressive';
    [key: string]: unknown;
  };
}

export interface SearchRequest {
  query: string;
  limit?: number;
  document_ids?: string[];
}

export interface SearchResult {
  chunk_id: string;
  document_id: string;
  content: string;
  highlighted_content: string;
  score: number;
  chunk_index: number;
  document_metadata: {
    id: string;
    filename: string;
    status: string;
    upload_timestamp: string;
    file_size: number;
    content_type: string;
  };
}

export interface SearchResponse {
  results: SearchResult[];
  query: string;
  total_results: number;
}

export interface PaginatedResponse<T> {
  documents?: T[];
  jobs?: T[];
  events?: T[];
  total: number;
  skip: number;
  limit: number;
}

export interface Metrics {
  total_documents: number;
  total_chunks: number;
  jobs_by_status: Record<string, number>;
  storage_used_bytes: number;
  recent_activity: Array<{
    id: string;
    job_id: string;
    event_type: string;
    timestamp: string;
  }>;
  system_health: 'healthy' | 'degraded';
}

export interface DocumentDetail extends Document {
  chunk_count: number;
  download_url?: string;
}

export interface JobDetail extends Job {
  latest_checkpoint?: JobState;
  event_count: number;
}
