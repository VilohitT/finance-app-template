"use client";

import Markdown from "./Markdown";
import ToolBlock, { ToolBlockData } from "./ToolBlock";

export type Block =
  | { type: "text"; text: string }
  | { type: "tool"; data: ToolBlockData };

export type MessageRecord = {
  id: string;
  role: "user" | "assistant" | "system";
  blocks: Block[];
  status?: "streaming" | "done";
};

export default function Message({ message }: { message: MessageRecord }) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-2xl bg-blue-600/20 border border-blue-600/30 rounded-lg px-4 py-2 text-sm text-gray-100 whitespace-pre-wrap">
          {message.blocks
            .filter((b): b is { type: "text"; text: string } => b.type === "text")
            .map((b) => b.text)
            .join("")}
        </div>
      </div>
    );
  }

  if (message.role === "system") {
    return (
      <div className="flex justify-center">
        <div className="text-xs text-gray-500 italic px-3 py-1">
          {message.blocks
            .filter((b): b is { type: "text"; text: string } => b.type === "text")
            .map((b) => b.text)
            .join("")}
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      {message.blocks.map((b, i) => {
        if (b.type === "tool") {
          return <ToolBlock key={b.data.id} tool={b.data} />;
        }
        return <Markdown key={i} text={b.text} />;
      })}
      {message.status === "streaming" && (
        <div className="text-gray-500 text-xs animate-pulse">▋</div>
      )}
    </div>
  );
}
