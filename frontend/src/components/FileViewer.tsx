"use client";

import { useEffect, useState } from "react";
import { fetchFileContent } from "@/lib/api";
import Markdown from "./Markdown";

type Props = {
  path: string | null;
};

export default function FileViewer({ path }: Props) {
  const [content, setContent] = useState<string | null>(null);
  const [size, setSize] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!path) {
      setContent(null);
      setError(null);
      setSize(null);
      return;
    }
    setLoading(true);
    setError(null);
    fetchFileContent(path)
      .then((res) => {
        setContent(res.content);
        setSize(res.size);
      })
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [path]);

  if (!path) {
    return (
      <div className="flex-1 flex items-center justify-center text-sm text-gray-500">
        Select a file from the tree.
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <div className="flex items-center justify-between border-b border-gray-800 px-4 py-2 text-xs">
        <code className="text-gray-300">{path}</code>
        {size !== null && <span className="text-gray-600">{size.toLocaleString()} bytes</span>}
      </div>
      <div className="flex-1 overflow-auto px-4 py-4">
        {loading && <div className="text-sm text-gray-500">loading…</div>}
        {error && (
          <div className="text-sm text-red-300 bg-red-500/10 border border-red-500/30 rounded p-3">
            {error}
          </div>
        )}
        {content !== null && !error && renderContent(path, content)}
      </div>
    </div>
  );
}

function renderContent(path: string, text: string): React.ReactNode {
  if (path.endsWith(".md")) {
    return <Markdown text={text} />;
  }
  if (path.endsWith(".json")) {
    let pretty = text;
    try {
      pretty = JSON.stringify(JSON.parse(text), null, 2);
    } catch {
      // not valid JSON; show as-is.
    }
    return (
      <pre className="text-xs font-mono text-gray-200 whitespace-pre-wrap">
        {pretty}
      </pre>
    );
  }
  return (
    <pre className="text-xs font-mono text-gray-200 whitespace-pre-wrap">{text}</pre>
  );
}
