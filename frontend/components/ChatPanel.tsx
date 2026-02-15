"use client";

import { useState } from "react";

import { API_BASE } from "../lib/api";

type Message = {
  role: "user" | "assistant";
  content: string;
};
const AI_TIMEOUT_MS = 60000; // 60s for cold start on Render free tier

export default function ChatPanel() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);

  const sendMessage = async () => {
    if (!input.trim() || streaming) return;
    const query = input.trim();
    setMessages((prev) => [...prev, { role: "user", content: query }]);
    setInput("");
    setStreaming(true);

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), AI_TIMEOUT_MS);

    try {
      const response = await fetch(`${API_BASE}/ai/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
        signal: controller.signal,
      });
      clearTimeout(timeout);
      const data = await response.json();
      const text = data?.response || "No response available.";
      setMessages((prev) => [...prev, { role: "assistant", content: text }]);
    } catch (error) {
      clearTimeout(timeout);
      const isTimeout = error instanceof Error && error.name === "AbortError";
      console.error("AI request failed", error);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: isTimeout
            ? "The backend is starting (Render free tier). Wait 30 seconds and try again."
            : "AI assistant is unavailable right now. Please try again.",
        },
      ]);
    } finally {
      setStreaming(false);
    }
  };

  return (
    <div className="rounded-xl border border-border/60 bg-white/5 p-6 shadow-[0_0_30px_rgba(124,58,237,0.12)] backdrop-blur">
      <h2 className="text-lg font-semibold text-ink">AI Assistant</h2>
      <p className="text-sm text-muted">
        Ask about the best discounts, cards, or nearby deals.
      </p>
      <div className="mt-4 space-y-4">
        {messages.map((message, index) => (
          <div
            key={`${message.role}-${index}`}
            className={`rounded-lg border border-white/10 p-3 text-sm text-ink ${
              message.role === "user"
                ? "bg-white/10 shadow-[0_0_18px_rgba(34,211,238,0.12)]"
                : "bg-primary/15 shadow-[0_0_18px_rgba(124,58,237,0.12)]"
            }`}
          >
            <strong className="block text-xs uppercase text-muted">
              {message.role}
            </strong>
            <p className="mt-1 whitespace-pre-line">{message.content}</p>
          </div>
        ))}
        {streaming && (
          <div className="rounded-lg border border-white/10 bg-primary/15 p-3 text-sm text-ink/80">
            Generating response...
          </div>
        )}
      </div>
      <div className="mt-4 flex gap-2">
        <input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          placeholder="Ask: Best food discounts in DHA Karachi"
          className="flex-1 rounded-md border border-border/60 bg-white/5 px-3 py-2 text-sm text-ink shadow-sm backdrop-blur placeholder:text-muted/80 focus:border-primary focus:outline-none"
        />
        <button
          onClick={sendMessage}
          className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-white shadow-[0_0_16px_rgba(124,58,237,0.5)] transition hover:brightness-110"
        >
          Send
        </button>
      </div>
    </div>
  );
}
