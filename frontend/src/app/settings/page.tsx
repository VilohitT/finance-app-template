"use client";

import { useEffect, useState } from "react";
import { fetchSettings, SettingsState, updateSettings } from "@/lib/api";

export default function SettingsPage() {
  const [settings, setSettings] = useState<SettingsState | null>(null);
  const [apiKey, setApiKey] = useState("");
  const [status, setStatus] = useState<string | null>(null);

  useEffect(() => {
    fetchSettings().then(setSettings).catch((e) => setStatus(String(e)));
  }, []);

  async function save() {
    setStatus("saving...");
    try {
      const next = await updateSettings({ anthropic_api_key: apiKey });
      setSettings(next);
      setApiKey("");
      setStatus("saved");
    } catch (e) {
      setStatus(String(e));
    }
  }

  return (
    <main className="min-h-screen p-8 max-w-2xl mx-auto">
      <h1 className="text-2xl font-semibold mb-2">Settings</h1>
      <p className="text-sm text-gray-400 mb-8">
        Configuration is stored locally in the mounted data volume (.config/settings.json, mode 0600).
      </p>

      <section className="mb-8">
        <h2 className="text-lg font-medium mb-3">Anthropic API key</h2>
        <p className="text-sm text-gray-400 mb-3">
          Currently: <code>{settings?.has_api_key ? "configured" : "not configured"}</code>
        </p>
        <input
          type="password"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          placeholder="sk-ant-..."
          className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-sm font-mono"
        />
        <button
          onClick={save}
          disabled={!apiKey}
          className="mt-3 px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed rounded text-sm"
        >
          Save key
        </button>
        {status && <p className="text-xs text-gray-400 mt-2">{status}</p>}
      </section>

      <section>
        <h2 className="text-lg font-medium mb-3">Defaults</h2>
        <ul className="text-sm text-gray-300 space-y-1">
          <li>Model: <code>{settings?.model}</code></li>
          <li>Effort: <code>{settings?.effort}</code></li>
        </ul>
      </section>
    </main>
  );
}
