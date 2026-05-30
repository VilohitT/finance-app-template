"use client";

import { useEffect, useRef, useState } from "react";
import type { Skill } from "@/lib/api";
import SlashPicker from "./SlashPicker";

type Props = {
  skills: Skill[];
  disabled: boolean;
  onSend: (input: { kind: "skill" | "message"; text: string; skill?: string }) => void;
};

export default function ChatInput({ skills, disabled, onSend }: Props) {
  const [value, setValue] = useState("");
  const [pickerOpen, setPickerOpen] = useState(false);
  const [highlighted, setHighlighted] = useState(0);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize the textarea.
  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = `${Math.min(ta.scrollHeight, 200)}px`;
  }, [value]);

  // Detect slash mode: only when input STARTS with a slash and has no whitespace
  // after the slash command yet. Once user types a space, we exit picker mode
  // (they're now writing the prompt body).
  const slashMatch = value.match(/^\/(\S*)$/);
  const slashQuery = slashMatch ? slashMatch[1] : null;
  const inPicker = slashQuery !== null;

  // Open picker when entering slash mode.
  useEffect(() => {
    setPickerOpen(inPicker);
    if (inPicker) setHighlighted(0);
  }, [inPicker]);

  const filteredSkills = skills.filter((s) =>
    s.name.toLowerCase().startsWith((slashQuery ?? "").toLowerCase()),
  );

  function send() {
    const trimmed = value.trim();
    if (!trimmed) return;
    // If input starts with /name (with optional message after), treat as skill.
    const m = trimmed.match(/^\/(\S+)(?:\s+([\s\S]*))?$/);
    if (m) {
      const skillName = m[1];
      const messageText = (m[2] ?? "").trim();
      // Only dispatch as skill if it's a valid skill name.
      if (skills.some((s) => s.name === skillName)) {
        onSend({ kind: "skill", text: messageText, skill: skillName });
        setValue("");
        setPickerOpen(false);
        return;
      }
    }
    onSend({ kind: "message", text: trimmed });
    setValue("");
    setPickerOpen(false);
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (pickerOpen && filteredSkills.length > 0) {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setHighlighted((h) => (h + 1) % filteredSkills.length);
        return;
      }
      if (e.key === "ArrowUp") {
        e.preventDefault();
        setHighlighted(
          (h) => (h - 1 + filteredSkills.length) % filteredSkills.length,
        );
        return;
      }
      if (e.key === "Enter" || e.key === "Tab") {
        e.preventDefault();
        const picked = filteredSkills[highlighted];
        if (picked) {
          setValue(`/${picked.name} `);
          setPickerOpen(false);
        }
        return;
      }
      if (e.key === "Escape") {
        e.preventDefault();
        setPickerOpen(false);
        return;
      }
    }
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  return (
    <div className="border-t border-gray-800 px-6 py-4 bg-gray-900/50">
      <div className="relative max-w-3xl mx-auto">
        {pickerOpen && (
          <SlashPicker
            skills={skills}
            query={slashQuery ?? ""}
            highlightedIndex={highlighted}
            onHighlight={setHighlighted}
            onSelect={(name) => {
              setValue(`/${name} `);
              setPickerOpen(false);
              textareaRef.current?.focus();
            }}
          />
        )}
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder={
            disabled
              ? "Connecting to backend…"
              : "Type / for a skill, or message the agent. Shift+Enter for newline."
          }
          disabled={disabled}
          rows={1}
          className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-sm text-gray-100 placeholder-gray-500 focus:outline-none focus:border-gray-500 resize-none disabled:opacity-50"
        />
        <div className="text-xs text-gray-600 mt-2 flex justify-between">
          <span>Enter to send · Shift+Enter for newline · / for skills</span>
          <button
            onClick={send}
            disabled={disabled || !value.trim()}
            className="text-blue-400 hover:text-blue-300 disabled:text-gray-700 disabled:cursor-not-allowed"
          >
            Send →
          </button>
        </div>
      </div>
    </div>
  );
}
