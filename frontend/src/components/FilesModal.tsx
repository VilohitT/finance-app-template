"use client";

import { useEffect, useState } from "react";
import FileTree from "./FileTree";
import FileViewer from "./FileViewer";

type Props = {
  open: boolean;
  onClose: () => void;
};

export default function FilesModal({ open, onClose }: Props) {
  const [selected, setSelected] = useState<string | null>(null);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape" && open) onClose();
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-gray-900 border border-gray-700 rounded-lg shadow-2xl w-full max-w-6xl h-[85vh] flex overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <aside className="w-64 border-r border-gray-800 overflow-y-auto bg-gray-900/80">
          <div className="px-4 py-2 border-b border-gray-800 text-xs uppercase tracking-wider text-gray-500">
            Project files
          </div>
          <FileTree selected={selected} onSelect={setSelected} />
        </aside>
        <FileViewer path={selected} />
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-200 text-2xl leading-none"
          aria-label="Close"
        >
          ×
        </button>
      </div>
    </div>
  );
}
