// Reanalysis Job Types (Feature 013)

export enum JobStatus {
  QUEUED = 'queued',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}

export enum TriggerType {
  MANUAL = 'manual',
  AUTOMATIC = 'automatic'
}

export interface DateRange {
  start?: string | null;
  end?: string | null;
}

export interface JobProgress {
  total_count: number;
  processed_count: number;
  percentage: number;
  last_checkpoint_id: string | null;
  estimated_time_remaining: number | null;  // in seconds
}

export interface JobStatistics {
  tools_detected: Record<string, number>;  // { tool_id: count }
  errors_count: number;
  categorized_count: number;
  uncategorized_count: number;
}

export interface JobErrorLog {
  doc_id: string;
  error: string;
  timestamp: string;
}

export interface ReanalysisJob {
  id: string;
  status: JobStatus;
  trigger_type: TriggerType;
  triggered_by: string;
  parameters: {
    date_range: DateRange | null;
    tool_ids: string[] | null;
    batch_size: number;
  };
  progress: JobProgress;
  statistics: JobStatistics;
  error_log: JobErrorLog[];
  start_time: string | null;
  end_time: string | null;
  created_at: string;
  reason?: string;  // For automatic jobs
}

export interface ReanalysisJobRequest {
  date_range?: DateRange;
  tool_ids?: string[];
  batch_size?: number;
}

export interface ReanalysisJobResponse {
  job_id: string;
  status: JobStatus;
  estimated_docs: number;
  message: string;
  poll_url: string;
}

export interface ReanalysisJobStatus {
  job_id: string;
  status: JobStatus;
  progress: JobProgress;
}

export interface ReanalysisJobList {
  jobs: ReanalysisJob[];
  total_count: number;
  limit: number;
  offset: number;
}
