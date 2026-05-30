import { WS_BASE } from "./api";

export type ServerEvent =
  | { type: "skill_started"; skill: string }
  | { type: "text"; delta: string }
  | { type: "thinking"; delta: string }
  | { type: "tool_use"; id: string; name: string; input: Record<string, unknown> }
  | { type: "tool_result"; tool_use_id: string; output: string; is_error: boolean }
  | { type: "usage"; input_tokens: number; output_tokens: number; cache_read_input_tokens: number | null; cache_creation_input_tokens: number | null }
  | { type: "done"; stop_reason: string }
  | { type: "error"; message: string }
  | { type: "session_reset" }
  | { type: "pong" };

export type ClientEvent =
  | { kind: "skill"; skill: string; message: string }
  | { kind: "message"; message: string }
  | { kind: "reset" }
  | { kind: "ping" };

export type ConnectionStatus = "connecting" | "open" | "closed" | "error";

export class ChatClient {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private explicitClose = false;
  onEvent: (event: ServerEvent) => void = () => {};
  onStatus: (status: ConnectionStatus) => void = () => {};

  constructor() {
    this.url = `${WS_BASE}/ws/chat`;
  }

  connect(): void {
    this.explicitClose = false;
    this.onStatus("connecting");
    try {
      this.ws = new WebSocket(this.url);
    } catch (err) {
      this.onStatus("error");
      this.scheduleReconnect();
      return;
    }
    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      this.onStatus("open");
    };
    this.ws.onmessage = (msg) => {
      try {
        const event = JSON.parse(msg.data) as ServerEvent;
        this.onEvent(event);
      } catch (err) {
        console.error("ws parse error", err, msg.data);
      }
    };
    this.ws.onclose = () => {
      this.ws = null;
      this.onStatus("closed");
      if (!this.explicitClose) this.scheduleReconnect();
    };
    this.ws.onerror = () => {
      this.onStatus("error");
    };
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    const delay = Math.min(1000 * 2 ** this.reconnectAttempts, 15000);
    this.reconnectAttempts += 1;
    this.reconnectTimer = setTimeout(() => this.connect(), delay);
  }

  send(event: ClientEvent): boolean {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return false;
    this.ws.send(JSON.stringify(event));
    return true;
  }

  close(): void {
    this.explicitClose = true;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    if (this.ws) this.ws.close();
  }
}
