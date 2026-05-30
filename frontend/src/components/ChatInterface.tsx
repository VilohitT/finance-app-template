"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { fetchSettings, fetchSkills, SettingsState, Skill } from "@/lib/api";
import { ChatClient, ConnectionStatus, ServerEvent } from "@/lib/ws";
import ChatInput from "./ChatInput";
import MessageList from "./MessageList";
import type { Block, MessageRecord } from "./Message";

function genId() {
  return Math.random().toString(36).slice(2, 11);
}

export default function ChatInterface() {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [settings, setSettings] = useState<SettingsState | null>(null);
  const [messages, setMessages] = useState<MessageRecord[]>([]);
  const [status, setStatus] = useState<ConnectionStatus>("connecting");
  const [activeSkill, setActiveSkill] = useState<string | null>(null);
  const clientRef = useRef<ChatClient | null>(null);

  // Load skills + settings once.
  useEffect(() => {
    fetchSkills().then(setSkills).catch(() => setSkills([]));
    fetchSettings().then(setSettings).catch(() => setSettings(null));
  }, []);

  // Connect WebSocket.
  useEffect(() => {
    const client = new ChatClient();
    clientRef.current = client;
    client.onStatus = setStatus;
    client.onEvent = handleEvent;
    client.connect();
    return () => {
      client.close();
      clientRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function handleEvent(event: ServerEvent) {
    switch (event.type) {
      case "skill_started":
        setActiveSkill(event.skill);
        // Add a system note that the skill started.
        appendSystem(`▸ Started /${event.skill}`);
        // Begin a new assistant message.
        appendAssistant();
        return;

      case "text":
        appendTextDelta(event.delta);
        return;

      case "thinking":
        // Phase 2: don't render thinking inline; could expose later as an
        // expandable block. Ignore for now.
        return;

      case "tool_use":
        addToolBlock({
          id: event.id,
          name: event.name,
          input: event.input,
          status: "running",
        });
        return;

      case "tool_result":
        completeToolBlock(event.tool_use_id, event.output, event.is_error);
        return;

      case "usage":
        // Could surface tokens in a status bar; skipping for Phase 2.
        return;

      case "done":
        markLastAssistantDone();
        return;

      case "error":
        appendSystem(`✗ ${event.message}`);
        markLastAssistantDone();
        return;

      case "session_reset":
        setActiveSkill(null);
        setMessages([]);
        return;
    }
  }

  function appendSystem(text: string) {
    setMessages((prev) => [
      ...prev,
      { id: genId(), role: "system", blocks: [{ type: "text", text }], status: "done" },
    ]);
  }

  function appendAssistant() {
    setMessages((prev) => [
      ...prev,
      { id: genId(), role: "assistant", blocks: [], status: "streaming" },
    ]);
  }

  function appendTextDelta(delta: string) {
    setMessages((prev) => {
      const next = [...prev];
      const last = next[next.length - 1];
      if (!last || last.role !== "assistant") {
        next.push({
          id: genId(),
          role: "assistant",
          blocks: [{ type: "text", text: delta }],
          status: "streaming",
        });
        return next;
      }
      const blocks = [...last.blocks];
      const lastBlock = blocks[blocks.length - 1];
      if (lastBlock && lastBlock.type === "text") {
        blocks[blocks.length - 1] = { type: "text", text: lastBlock.text + delta };
      } else {
        blocks.push({ type: "text", text: delta });
      }
      next[next.length - 1] = { ...last, blocks };
      return next;
    });
  }

  function addToolBlock(tool: {
    id: string;
    name: string;
    input: Record<string, unknown>;
    status: "running";
  }) {
    setMessages((prev) => {
      const next = [...prev];
      let last = next[next.length - 1];
      if (!last || last.role !== "assistant") {
        // Should not happen, but be defensive.
        next.push({ id: genId(), role: "assistant", blocks: [], status: "streaming" });
        last = next[next.length - 1];
      }
      const newBlock: Block = { type: "tool", data: tool };
      next[next.length - 1] = { ...last, blocks: [...last.blocks, newBlock] };
      return next;
    });
  }

  function completeToolBlock(toolUseId: string, output: string, isError: boolean) {
    setMessages((prev) => {
      const next = [...prev];
      for (let i = next.length - 1; i >= 0; i--) {
        const msg = next[i];
        if (msg.role !== "assistant") continue;
        const idx = msg.blocks.findIndex(
          (b) => b.type === "tool" && b.data.id === toolUseId,
        );
        if (idx === -1) continue;
        const blocks = [...msg.blocks];
        const existing = blocks[idx];
        if (existing.type === "tool") {
          blocks[idx] = {
            type: "tool",
            data: {
              ...existing.data,
              status: isError ? "error" : "done",
              result: output,
            },
          };
        }
        next[i] = { ...msg, blocks };
        break;
      }
      return next;
    });
  }

  function markLastAssistantDone() {
    setMessages((prev) => {
      const next = [...prev];
      for (let i = next.length - 1; i >= 0; i--) {
        if (next[i].role === "assistant") {
          next[i] = { ...next[i], status: "done" };
          break;
        }
      }
      return next;
    });
  }

  function handleSend(input: { kind: "skill" | "message"; text: string; skill?: string }) {
    const client = clientRef.current;
    if (!client) return;

    // Add user message to local state.
    const userText = input.kind === "skill"
      ? input.text
        ? `/${input.skill} ${input.text}`
        : `/${input.skill}`
      : input.text;
    setMessages((prev) => [
      ...prev,
      {
        id: genId(),
        role: "user",
        blocks: [{ type: "text", text: userText }],
        status: "done",
      },
    ]);

    if (input.kind === "skill" && input.skill) {
      client.send({ kind: "skill", skill: input.skill, message: input.text });
    } else {
      // Need a new assistant message for the streaming text.
      appendAssistant();
      client.send({ kind: "message", message: input.text });
    }
  }

  function handleReset() {
    clientRef.current?.send({ kind: "reset" });
  }

  const noApiKey = settings?.has_api_key === false;

  return (
    <div className="h-screen flex flex-col">
      <header className="border-b border-gray-800 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h1 className="text-lg font-semibold">finance-app</h1>
          {activeSkill && (
            <span className="text-xs text-gray-500">
              active: <code className="text-blue-300">/{activeSkill}</code>
            </span>
          )}
        </div>
        <div className="flex items-center gap-4 text-xs">
          <ConnectionDot status={status} />
          {activeSkill && (
            <button
              onClick={handleReset}
              className="text-gray-400 hover:text-gray-200"
            >
              reset
            </button>
          )}
          <Link href="/settings" className="text-gray-400 hover:text-gray-200">
            settings
          </Link>
        </div>
      </header>

      {noApiKey && (
        <div className="bg-yellow-500/10 border-b border-yellow-500/30 px-6 py-2 text-xs text-yellow-200">
          No Anthropic API key configured.{" "}
          <Link href="/settings" className="underline">
            Add one in settings
          </Link>{" "}
          to start using the agent.
        </div>
      )}

      <MessageList messages={messages} />

      <ChatInput
        skills={skills}
        disabled={status !== "open"}
        onSend={handleSend}
      />
    </div>
  );
}

function ConnectionDot({ status }: { status: ConnectionStatus }) {
  const color =
    status === "open"
      ? "bg-green-500"
      : status === "connecting"
        ? "bg-yellow-500 animate-pulse"
        : "bg-red-500";
  const label =
    status === "open"
      ? "connected"
      : status === "connecting"
        ? "connecting…"
        : status === "error"
          ? "error"
          : "disconnected";
  return (
    <span className="flex items-center gap-1.5 text-gray-500">
      <span className={`inline-block w-2 h-2 rounded-full ${color}`} />
      {label}
    </span>
  );
}
