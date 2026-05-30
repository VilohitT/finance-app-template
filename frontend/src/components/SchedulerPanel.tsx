"use client";

import { useEffect, useState } from "react";
import {
  fetchSchedulerStatus,
  SchedulerJob,
  SchedulerStatus,
  triggerSchedulerJob,
  updateSettings,
} from "@/lib/api";

type Props = {
  enabled: boolean;
  onToggle: (next: boolean) => void;
};

export default function SchedulerPanel({ enabled, onToggle }: Props) {
  const [status, setStatus] = useState<SchedulerStatus | null>(null);
  const [running, setRunning] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void reload();
  }, []);

  async function reload() {
    try {
      setStatus(await fetchSchedulerStatus());
      setError(null);
    } catch (e) {
      setError(String(e));
    }
  }

  async function toggle() {
    try {
      const next = !enabled;
      await updateSettings({ daily_nav_enabled: next });
      onToggle(next);
      await reload();
    } catch (e) {
      setError(String(e));
    }
  }

  async function runNow(jobId: string) {
    setRunning((s) => new Set(s).add(jobId));
    try {
      const next = await triggerSchedulerJob(jobId);
      setStatus(next);
      setError(null);
    } catch (e) {
      setError(String(e));
    } finally {
      setRunning((s) => {
        const next = new Set(s);
        next.delete(jobId);
        return next;
      });
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-medium">Scheduler</h2>
          <p className="text-xs text-gray-500 mt-1">
            Runs nightly NAV refresh + monthly recurring tranche generator
            inside the container. Times are Asia/Kolkata.
          </p>
        </div>
        <button
          onClick={toggle}
          className={`px-3 py-1.5 rounded text-sm border ${
            enabled
              ? "bg-green-600/20 border-green-500/40 text-green-200"
              : "bg-gray-800 border-gray-700 text-gray-300"
          }`}
        >
          {enabled ? "Enabled" : "Disabled"}
        </button>
      </div>

      {error && (
        <div className="mb-4 text-xs text-red-300 bg-red-500/10 border border-red-500/30 rounded p-2">
          {error}
        </div>
      )}

      {status === null ? (
        <p className="text-sm text-gray-500">Loading scheduler status…</p>
      ) : (
        <div className="space-y-3">
          {status.jobs.map((job) => (
            <JobRow
              key={job.id}
              job={job}
              running={running.has(job.id)}
              onRun={() => runNow(job.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function JobRow({
  job,
  running,
  onRun,
}: {
  job: SchedulerJob;
  running: boolean;
  onRun: () => void;
}) {
  const [showLog, setShowLog] = useState(false);
  const last = job.last_run;

  return (
    <div className="border border-gray-800 rounded p-3">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="font-mono text-sm text-gray-200">{job.id}</div>
          <div className="text-xs text-gray-500 mt-0.5">{job.description}</div>
          <div className="text-xs text-gray-400 mt-2 space-y-0.5">
            <div>
              <span className="text-gray-600">Next:</span>{" "}
              {job.scheduled ? formatDate(job.next_run) : <span className="text-gray-600">— (disabled)</span>}
            </div>
            {last && (
              <div>
                <span className="text-gray-600">Last:</span>{" "}
                {formatDate(last.started_at)} —{" "}
                <span
                  className={
                    last.status === "success"
                      ? "text-green-400"
                      : last.status === "failed"
                        ? "text-red-400"
                        : "text-yellow-400"
                  }
                >
                  {last.status}
                </span>
                {last.exit_code !== null && (
                  <span className="text-gray-600"> (exit {last.exit_code})</span>
                )}
              </div>
            )}
          </div>
        </div>
        <button
          onClick={onRun}
          disabled={running}
          className="text-xs px-3 py-1 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:cursor-not-allowed rounded text-white"
        >
          {running ? "Running…" : "Run now"}
        </button>
      </div>
      {last && last.output_tail && (
        <div className="mt-2">
          <button
            onClick={() => setShowLog(!showLog)}
            className="text-xs text-gray-500 hover:text-gray-300"
          >
            {showLog ? "Hide" : "Show"} last output
          </button>
          {showLog && (
            <pre className="mt-2 text-xs font-mono text-gray-300 bg-black/30 p-2 rounded max-h-48 overflow-auto whitespace-pre-wrap">
              {last.output_tail}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}
