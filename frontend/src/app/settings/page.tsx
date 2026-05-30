"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { fetchSettings, SettingsState, updateSettings } from "@/lib/api";
import SchedulerPanel from "@/components/SchedulerPanel";

export default function SettingsPage() {
  const [settings, setSettings] = useState<SettingsState | null>(null);
  const [apiKey, setApiKey] = useState("");
  const [status, setStatus] = useState<string | null>(null);

  useEffect(() => {
    fetchSettings().then(setSettings).catch((e) => setStatus(String(e)));
  }, []);

  async function saveKey() {
    if (!apiKey) return;
    setStatus("saving…");
    try {
      const next = await updateSettings({ anthropic_api_key: apiKey });
      setSettings(next);
      setApiKey("");
      setStatus("saved");
    } catch (e) {
      setStatus(String(e));
    }
  }

  async function clearKey() {
    setStatus("clearing…");
    try {
      // Set empty string explicitly; backend strips empty values, so we send a
      // sentinel by setting api key to a single space then re-saving.
      // Simpler: just direct call with empty body — but our backend ignores
      // empty key. Workaround: delete the settings file by writing an empty
      // object — but we don't have a delete endpoint. For Phase 4 we'll
      // accept that the user has to restart the container to forget the key.
      setStatus("To remove the saved key, delete data/.config/settings.json on disk.");
    } catch (e) {
      setStatus(String(e));
    }
  }

  return (
    <main className="min-h-screen px-6 py-8">
      <div className="max-w-3xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-2xl font-semibold">Settings</h1>
          <Link href="/" className="text-sm text-gray-400 hover:text-gray-200">
            ← back to chat
          </Link>
        </div>

        <section className="mb-12">
          <h2 className="text-lg font-medium mb-3">Anthropic API key</h2>
          <p className="text-xs text-gray-500 mb-3">
            Stored locally in your data volume at <code>.config/settings.json</code> (mode 0600).
            Currently: <code>{settings?.has_api_key ? "configured" : "not configured"}</code>.
          </p>
          <div className="flex gap-2">
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="sk-ant-..."
              className="flex-1 px-3 py-2 bg-gray-900 border border-gray-700 rounded text-sm font-mono"
            />
            <button
              onClick={saveKey}
              disabled={!apiKey}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed rounded text-sm"
            >
              Save
            </button>
          </div>
          {status && <p className="text-xs text-gray-400 mt-2">{status}</p>}
          {settings?.has_api_key && (
            <button
              onClick={clearKey}
              className="text-xs text-gray-500 hover:text-gray-300 underline mt-3"
            >
              How to remove the saved key?
            </button>
          )}
        </section>

        <section className="mb-12">
          <h2 className="text-lg font-medium mb-3">Model defaults</h2>
          <p className="text-xs text-gray-500 mb-3">
            Adaptive thinking is always on. Changes apply to the next skill
            invocation.
          </p>

          <div className="space-y-4">
            <div>
              <label className="block text-xs uppercase tracking-wider text-gray-500 mb-1.5">
                Model
              </label>
              <select
                value={settings?.model ?? ""}
                onChange={async (e) => {
                  if (!settings) return;
                  const next = await updateSettings({ model: e.target.value });
                  setSettings(next);
                }}
                className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-gray-100"
              >
                {settings?.available_models?.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs uppercase tracking-wider text-gray-500 mb-1.5">
                Effort
              </label>
              <select
                value={settings?.effort ?? ""}
                onChange={async (e) => {
                  if (!settings) return;
                  const next = await updateSettings({ effort: e.target.value });
                  setSettings(next);
                }}
                className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-gray-100"
              >
                {settings?.available_efforts?.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.label}
                  </option>
                ))}
              </select>
              <p className="text-xs text-gray-500 mt-1.5">
                Higher effort = more tool calls + deeper reasoning but more
                tokens. <code>max</code> only works on Opus models.
              </p>
            </div>
          </div>
        </section>

        <section>
          <SchedulerPanel
            enabled={settings?.daily_nav_enabled ?? true}
            onToggle={(next) =>
              setSettings((prev) =>
                prev ? { ...prev, daily_nav_enabled: next } : prev,
              )
            }
          />
        </section>
      </div>
    </main>
  );
}
