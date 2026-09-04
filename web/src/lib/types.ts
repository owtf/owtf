// Wire records mirror internal/model. Keep fields named as the API returns them.
export interface Session {
  id: string;
  name: string;
  created_at: string;
}
export interface Target {
  id: string;
  session_id: string;
  value: string;
  kind: string;
  scope: boolean;
}
export interface Technique {
  code: string;
  title: string;
  hint?: string;
  reference?: string;
}
export interface PluginInput {
  name: string;
  type: string;
  description?: string;
  required?: boolean;
  default?: unknown;
  choices?: string[];
  minimum?: number;
  maximum?: number;
}
export interface Plugin {
  id: string;
  title: string;
  description: string;
  group: string;
  type: string;
  runtime_type: string;
  techniques: Technique[];
  inputs: PluginInput[];
  availability: string;
  reason?: string;
}
export interface Task {
  id: string;
  run_id: string;
  target_id: string;
  plugin_id: string;
  status: string;
  position: number;
  techniques: Technique[];
  created_at: string;
  started_at?: string;
  ended_at?: string;
  error?: string;
}
export interface Event {
  id: number;
  task_id: string;
  stream: string;
  message: string;
  created_at: string;
}
export interface Review {
  task_id: string;
  rank: string;
  disposition: string;
  notes: string;
}
export interface ReviewEvent extends Review {
  id: number;
  created_at: string;
}
export interface Artifact {
  id: string;
  task_id: string;
  name: string;
  media_type: string;
  size: number;
}
export interface Transaction {
  id: string;
  task_id?: string;
  target_id: string;
  method: string;
  url: string;
  status_code: number;
  request_headers: string;
  response_headers: string;
  request_body_artifact_id?: string;
  response_body_artifact_id?: string;
  duration_ms: number;
}
export interface Observation {
  id: string;
  task_id: string;
  kind: string;
  data: string;
}
export interface Finding {
  id: string;
  task_id: string;
  title: string;
  severity: string;
  description: string;
}
export interface Report {
  target: Target;
  tasks: Task[];
  plugin_output_reviews: Review[];
  plugin_output_review_events: ReviewEvent[];
  artifacts: Artifact[];
  transactions: Transaction[];
  events: Event[];
  observations: Observation[];
  findings: Finding[];
  urls: { url: string; visited: boolean; scope: boolean }[];
}
export interface Worker {
  id: string;
  status: string;
  task_id?: string;
  target_id?: string;
  plugin_id?: string;
  completed: number;
  failed: number;
  cancelled: number;
}
export interface Page<T> {
  data: T[];
  records_total: number;
  records_filtered: number;
}
export const ranks = [
  "unranked",
  "passing",
  "informational",
  "low",
  "medium",
  "high",
  "critical",
];
export const dispositions = [
  "open",
  "confirmed",
  "false_positive",
  "accepted_risk",
];
