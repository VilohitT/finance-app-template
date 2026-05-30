// Resolves the backend base URL. In dev, the backend runs on :8000 (a different
// port from the Next.js dev server). In production, the backend serves the
// frontend statically, so same-origin works.

const isDev =
  typeof window !== "undefined" && window.location.port === "3000";

export const API_BASE = isDev ? "http://localhost:8000" : "";
export const WS_BASE = isDev
  ? "ws://localhost:8000"
  : typeof window !== "undefined"
    ? `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}`
    : "";

export interface Skill {
  name: string;
  description: string;
}

export async function fetchSkills(): Promise<Skill[]> {
  const res = await fetch(`${API_BASE}/api/skills`);
  if (!res.ok) throw new Error(`Skills fetch failed: ${res.status}`);
  return res.json();
}

export interface SelectOption {
  id: string;
  label: string;
}

export interface SettingsState {
  has_api_key: boolean;
  model: string;
  effort: string;
  daily_nav_enabled: boolean;
  available_models: SelectOption[];
  available_efforts: SelectOption[];
}

export async function fetchSettings(): Promise<SettingsState> {
  const res = await fetch(`${API_BASE}/api/settings`);
  if (!res.ok) throw new Error(`Settings fetch failed: ${res.status}`);
  return res.json();
}

export async function updateSettings(
  patch: Partial<SettingsState & { anthropic_api_key: string }>,
): Promise<SettingsState> {
  const res = await fetch(`${API_BASE}/api/settings`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(patch),
  });
  if (!res.ok) throw new Error(`Settings update failed: ${res.status}`);
  return res.json();
}

export interface FileEntry {
  path: string;
  is_dir: boolean;
  size: number | null;
}

export async function listFiles(path = ""): Promise<FileEntry[]> {
  const url = new URL(`${API_BASE}/api/files`, window.location.origin);
  if (path) url.searchParams.set("path", path);
  const res = await fetch(url.toString());
  if (!res.ok) throw new Error(`Files list failed: ${res.status}`);
  return res.json();
}

export interface FileContent {
  path: string;
  content: string;
  size: number;
}

export async function fetchFileContent(path: string): Promise<FileContent> {
  const url = new URL(`${API_BASE}/api/files/content`, window.location.origin);
  url.searchParams.set("path", path);
  const res = await fetch(url.toString());
  if (!res.ok) {
    if (res.status === 415) throw new Error("Binary file (not text)");
    if (res.status === 404) throw new Error("File not found");
    throw new Error(`File fetch failed: ${res.status}`);
  }
  return res.json();
}

export interface JobRun {
  started_at: string;
  finished_at: string | null;
  status: "running" | "success" | "failed";
  exit_code: number | null;
  output_tail: string;
}

export interface SchedulerJob {
  id: string;
  description: string;
  next_run: string | null;
  scheduled: boolean;
  last_run: JobRun | null;
  history: JobRun[];
}

export interface SchedulerStatus {
  enabled: boolean;
  jobs: SchedulerJob[];
}

export async function fetchSchedulerStatus(): Promise<SchedulerStatus> {
  const res = await fetch(`${API_BASE}/api/scheduler`);
  if (!res.ok) throw new Error(`Scheduler status failed: ${res.status}`);
  return res.json();
}

export async function triggerSchedulerJob(jobId: string): Promise<SchedulerStatus> {
  const res = await fetch(`${API_BASE}/api/scheduler/run/${jobId}`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(`Trigger failed: ${res.status}`);
  return res.json();
}
