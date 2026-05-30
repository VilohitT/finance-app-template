"use client";

import { useEffect } from "react";
import type { Skill } from "@/lib/api";

type Props = {
  skills: Skill[];
  query: string;
  highlightedIndex: number;
  onHighlight: (index: number) => void;
  onSelect: (skill: string) => void;
};

export default function SlashPicker({
  skills,
  query,
  highlightedIndex,
  onHighlight,
  onSelect,
}: Props) {
  const filtered = skills.filter((s) =>
    s.name.toLowerCase().startsWith(query.toLowerCase()),
  );

  useEffect(() => {
    if (highlightedIndex >= filtered.length && filtered.length > 0) {
      onHighlight(0);
    }
  }, [filtered.length, highlightedIndex, onHighlight]);

  if (filtered.length === 0) {
    return (
      <div className="absolute bottom-full left-0 right-0 mb-2 bg-gray-900 border border-gray-700 rounded shadow-lg p-3 text-xs text-gray-500">
        No matching skills.
      </div>
    );
  }

  return (
    <div className="absolute bottom-full left-0 right-0 mb-2 bg-gray-900 border border-gray-700 rounded shadow-lg max-h-64 overflow-y-auto">
      {filtered.map((s, i) => (
        <button
          key={s.name}
          onMouseEnter={() => onHighlight(i)}
          onClick={() => onSelect(s.name)}
          className={`w-full text-left px-3 py-2 border-b border-gray-800 last:border-b-0 ${
            i === highlightedIndex ? "bg-gray-800" : ""
          }`}
        >
          <div className="font-mono text-sm text-blue-300">/{s.name}</div>
          <div className="text-xs text-gray-500 line-clamp-2">
            {s.description}
          </div>
        </button>
      ))}
    </div>
  );
}
