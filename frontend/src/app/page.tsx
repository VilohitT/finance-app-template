"use client";

import { useEffect, useState } from "react";
import { fetchSettings, fetchSkills, SettingsState, Skill } from "@/lib/api";

export default function Home() {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [settings, setSettings] = useState<SettingsState | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([fetchSkills(), fetchSettings()])
      .then(([sk, st]) => {
        setSkills(sk);
        setSettings(st);
      })
      .catch((e) => setError(String(e)));
  }, []);

  return (
    <main className="min-h-screen p-8 max-w-3xl mx-auto">
      <h1 className="text-2xl font-semibold mb-2">finance-app</h1>
      <p className="text-sm text-gray-400 mb-8">
        Indian-context personal investment planning. Phase 1 scaffold — chat UI
        wires up in the next iteration.
      </p>

      {error && (
        <div className="border border-red-500/40 bg-red-500/10 text-red-200 p-3 rounded mb-6">
          {error}
        </div>
      )}

      <section className="mb-8">
        <h2 className="text-lg font-medium mb-3">Backend status</h2>
        {settings ? (
          <ul className="text-sm text-gray-300 space-y-1">
            <li>API key configured: <span className={settings.has_api_key ? "text-green-400" : "text-yellow-400"}>{settings.has_api_key ? "yes" : "no — visit /settings"}</span></li>
            <li>Model: <code className="text-gray-100">{settings.model}</code></li>
            <li>Effort: <code className="text-gray-100">{settings.effort}</code></li>
          </ul>
        ) : (
          <p className="text-sm text-gray-500">Loading…</p>
        )}
      </section>

      <section>
        <h2 className="text-lg font-medium mb-3">Available skills</h2>
        {skills.length === 0 ? (
          <p className="text-sm text-gray-500">No skills detected. Check SKILLS_ROOT.</p>
        ) : (
          <ul className="space-y-3">
            {skills.map((s) => (
              <li key={s.name} className="border border-gray-700 rounded p-3">
                <div className="font-mono text-sm text-blue-300">/{s.name}</div>
                <div className="text-xs text-gray-400 mt-1 line-clamp-3">
                  {s.description || "(no description)"}
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <footer className="mt-12 text-xs text-gray-600">
        Chat UI lands in Phase 2. The agent loop, tool registry, and WebSocket transport are wired on the backend.
      </footer>
    </main>
  );
}
