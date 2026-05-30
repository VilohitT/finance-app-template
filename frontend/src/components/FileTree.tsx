"use client";

import { useEffect, useState } from "react";
import { FileEntry, listFiles } from "@/lib/api";

type Props = {
  selected: string | null;
  onSelect: (path: string) => void;
};

const ROOT_KEY = "__root__";

export default function FileTree({ selected, onSelect }: Props) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set([ROOT_KEY]));
  const [children, setChildren] = useState<Record<string, FileEntry[]>>({});
  const [loading, setLoading] = useState<Set<string>>(new Set());
  const [error, setError] = useState<Record<string, string>>({});

  // Load root on mount.
  useEffect(() => {
    void loadDir("");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function loadDir(path: string) {
    const key = path || ROOT_KEY;
    if (children[key] || loading.has(key)) return;
    setLoading((s) => new Set(s).add(key));
    try {
      const entries = await listFiles(path);
      setChildren((c) => ({ ...c, [key]: entries }));
    } catch (e) {
      setError((er) => ({ ...er, [key]: String(e) }));
    } finally {
      setLoading((s) => {
        const next = new Set(s);
        next.delete(key);
        return next;
      });
    }
  }

  function toggle(path: string) {
    const key = path || ROOT_KEY;
    setExpanded((s) => {
      const next = new Set(s);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
    if (!children[key]) void loadDir(path);
  }

  function renderEntries(dirPath: string, depth: number): React.ReactNode {
    const key = dirPath || ROOT_KEY;
    if (error[key]) {
      return (
        <div className="text-xs text-red-400 px-3 py-1">{error[key]}</div>
      );
    }
    const entries = children[key];
    if (!entries) {
      if (loading.has(key)) {
        return <div className="text-xs text-gray-500 px-3 py-1">loading…</div>;
      }
      return null;
    }
    return entries.map((e) => {
      const isExpanded = expanded.has(e.path);
      if (e.is_dir) {
        return (
          <div key={e.path}>
            <button
              onClick={() => toggle(e.path)}
              className="w-full flex items-center gap-1 text-left px-2 py-0.5 text-sm text-gray-200 hover:bg-gray-800/50 rounded"
              style={{ paddingLeft: `${depth * 12 + 8}px` }}
            >
              <span className="text-gray-500 w-3">{isExpanded ? "▾" : "▸"}</span>
              <span className="text-yellow-200">📁</span>
              <span>{basename(e.path)}</span>
            </button>
            {isExpanded && renderEntries(e.path, depth + 1)}
          </div>
        );
      }
      const isSelected = e.path === selected;
      return (
        <button
          key={e.path}
          onClick={() => onSelect(e.path)}
          className={`w-full flex items-center gap-1 text-left px-2 py-0.5 text-sm rounded ${
            isSelected
              ? "bg-blue-600/30 text-blue-100"
              : "text-gray-300 hover:bg-gray-800/50"
          }`}
          style={{ paddingLeft: `${depth * 12 + 24}px` }}
        >
          <span>{fileIcon(e.path)}</span>
          <span className="truncate flex-1">{basename(e.path)}</span>
          {e.size !== null && (
            <span className="text-xs text-gray-600">{humanSize(e.size)}</span>
          )}
        </button>
      );
    });
  }

  return <div className="py-2">{renderEntries("", 0)}</div>;
}

function basename(path: string): string {
  const idx = path.lastIndexOf("/");
  return idx === -1 ? path : path.slice(idx + 1);
}

function fileIcon(path: string): string {
  if (path.endsWith(".md")) return "📄";
  if (path.endsWith(".json")) return "🔧";
  if (path.endsWith(".py")) return "🐍";
  if (path.endsWith(".db")) return "💾";
  if (path.endsWith(".txt")) return "📋";
  if (path.endsWith(".plist")) return "⚙️";
  return "📃";
}

function humanSize(bytes: number): string {
  if (bytes < 1024) return `${bytes}B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}K`;
  return `${(bytes / 1024 / 1024).toFixed(1)}M`;
}
