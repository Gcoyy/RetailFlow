
export type Status =
  | "Success"
  | "Running"
  | "Failed"
  | "Paused"
  | "Warning"
  | "Disconnected"
  | "Cancelled"
  | "Connected";

export type Severity = "Critical" | "High" | "Medium" | "Low";

const API_BASE_URL = "http://127.0.0.1:8000/api";

// Types describe the data returned by FastAPI.

export interface DashboardSummary {
  total_sources: number;
  total_pipelines: number;
  total_records: number;
  valid_records: number;
  failed_records: number;
  total_quality_issues: number;
  success_rate: number;
  latest_run_status: string;
}

export interface DataSource {
  id: number;
  name: string;
  type: string;
  status: Status;
  sync: string;
  records: string;
  created: string | null;
}

export interface Pipeline {
  id: number;
  name: string;
  source: string;
  destination: string;
  status: Status;
  duration: string;
  records: string;
  rate: string;
}

export interface Execution {
  id: string;
  pipeline: string;
  status: Status;
  records: string;
  duration: string;
  start: string | null;
  trigger: string;
}

export interface QualityIssue {
  id: string;
  dataset: string;
  field: string;
  rule: string;
  error: string;
  severity: Severity;
  date: string | null;
  status: string;
}

export interface PipelineLog {
  id: number;
  time: string | null;
  level: string;
  pipeline: string;
  execution: string;
  message: string;
  component: string;
}

// These variables start empty and are populated by refreshData().

export let summary: DashboardSummary = {
  total_sources: 0,
  total_pipelines: 0,
  total_records: 0,
  valid_records: 0,
  failed_records: 0,
  total_quality_issues: 0,
  success_rate: 0,
  latest_run_status: "None",
};

export let sources: DataSource[] = [];
export let pipelines: Pipeline[] = [];
export let executions: Execution[] = [];
export let qualityIssues: QualityIssue[] = [];
export let logs: PipelineLog[] = [];
export let activity: string[] = [];

// Reusable function for communicating with FastAPI.

async function apiGet<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`);

  if (!response.ok) {
    throw new Error(
      `API request failed: ${response.status} ${response.statusText}`
    );
  }

  return response.json() as Promise<T>;
}

// Fetch all dashboard data from the backend.

export async function refreshData(): Promise<void> {
  const [
    dashboardData,
    sourceData,
    pipelineData,
    issueData,
    executionData,
    logData,
    activityData,
  ] = await Promise.all([
    apiGet<DashboardSummary>("/dashboard/summary"),
    apiGet<DataSource[]>("/sources"),
    apiGet<Pipeline[]>("/pipelines"),
    apiGet<QualityIssue[]>("/quality/issues"),
    apiGet<Execution[]>("/executions"),
    apiGet<PipelineLog[]>("/logs"),
    apiGet<string[]>("/activity"),
  ]);

  summary = dashboardData;
  sources = sourceData;
  pipelines = pipelineData;
  qualityIssues = issueData;
  executions = executionData;
  logs = logData;
  activity = activityData;
}
