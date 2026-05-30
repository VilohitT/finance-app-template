"use client";

import { useState } from "react";

export type ToolBlockData = {
  id: string;
  name: string;
  input: Record<string, unknown>;
  status: "running" | "done" | "error";
  result?: string;
};

const ICONS: Record<string, string> = {
  read_file: "📖",
  write_file: "✍️",
  edit_file: "✏️",
  bash: "▶",
};

function summarizeInput(name: string, input: Record<string, unknown>): string {
  if (name === "read_file" || name === "write_file" || name === "edit_file") {
    return String(input.path ?? "");
  }
  if (name === "bash") {
    const cmd = String(input.command ?? "");
    return cmd.length > 60 ? cmd.slice(0, 60) + "…" : cmd;
  }
  return JSON.stringify(input).slice(0, 60);
}

export default function ToolBlock({ tool }: { tool: ToolBlockData }) {
  const [expanded, setExpanded] = useState(false);
  const icon = ICONS[tool.name] ?? "🔧";
  const summary = summarizeInput(tool.name, tool.input);
  const isError = tool.status === "error";
  const isRunning = tool.status === "running";

  return (
    <div
      className={`my-2 rounded border text-xs ${
        isError ? "border-red-500/40 bg-red-500/5" : "border-gray-700 bg-gray-800/40"
      }`}
    >
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-gray-700/30 rounded"
      >
        <span>{icon}</span>
        <span className="font-mono text-gray-300">{tool.name}</span>
        <span className="text-gray-500 truncate flex-1">{summary}</span>
        {isRunning ? (
          <span className="text-yellow-400 animate-pulse">running…</span>
        ) : isError ? (
          <span className="text-red-400">error</span>
        ) : (
          <span className="text-gray-500">{expanded ? "▾" : "▸"}</span>
        )}
      </button>
      {expanded && (
        <div className="px-3 pb-2 border-t border-gray-700">
          {Object.keys(tool.input).length > 0 && (
            <div className="mt-2">
              <div className="text-gray-500 mb-1">input:</div>
              <pre className="text-gray-300 overflow-x-auto whitespace-pre-wrap">
                {JSON.stringify(tool.input, null, 2)}
              </pre>
            </div>
          )}
          {tool.result !== undefined && (
            <div className="mt-2">
              <div className="text-gray-500 mb-1">
                {isError ? "error:" : "output:"}
              </div>
              <pre className="text-gray-300 overflow-x-auto whitespace-pre-wrap max-h-64">
                {tool.result}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
