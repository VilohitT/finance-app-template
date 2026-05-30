"use client";

import { useEffect, useRef } from "react";
import Message, { MessageRecord } from "./Message";

export default function MessageList({ messages }: { messages: MessageRecord[] }) {
  const endRef = useRef<HTMLDivElement>(null);
  // Auto-scroll to bottom on new content. We pin to bottom unless the user has
  // scrolled away; for the MVP just always scroll on update.
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
      <div className="max-w-3xl mx-auto space-y-6">
        {messages.map((m) => (
          <Message key={m.id} message={m} />
        ))}
        <div ref={endRef} />
      </div>
    </div>
  );
}
