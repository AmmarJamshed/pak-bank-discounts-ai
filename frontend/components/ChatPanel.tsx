"use client";

import { useEffect, useRef, useState } from "react";

type Message = {
  role: "user" | "assistant";
  content: string;
};

export default function ChatPanel() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const eventRef = useRef<EventSource | null>(null);
  const timeoutRef = useRef<number | null>(null);
  const apiBase =
    process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

  useEffect(() => {
    return () => {
      eventRef.current?.close();
      if (timeoutRef.current) {
        window.clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const fetchFallback = async (query: string) => {
    try {
      const response = await fetch(`${apiBase}/ai/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query })
      });
      const data = await response.json();
      const text = data?.response || "No response available.";
      setMessages((prev) => [...prev, { role: "assistant", content: text }]);
    } catch (error) {
      console.error("AI fallback failed", error);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "AI assistant is unavailable right now. Please try again."
        }
      ]);
    } finally {
      setStreaming(false);
    }
  };

  const sendMessage = () => {
    if (!input.trim() || streaming) return;
    const query = input.trim();
    setMessages((prev) => [...prev, { role: "user", content: query }]);
    setInput("");
    setStreaming(true);

    const url = new URL(`${apiBase}/ai/stream`);
    url.searchParams.set("query", query);
    const source = new EventSource(url.toString());
    eventRef.current = source;

    let assistantText = "";
    let hasChunk = false;
    source.onmessage = (event) => {
      if (event.data === "[DONE]") {
        const decoded = assistantText.replace(/\\n/g, "\n");
        setMessages((prev) => [...prev, { role: "assistant", content: decoded }]);
        setStreaming(false);
        source.close();
        return;
      }
      if (!hasChunk) {
        hasChunk = true;
        if (timeoutRef.current) {
          window.clearTimeout(timeoutRef.current);
        }
      }
      assistantText += event.data;
    };
    source.onerror = () => {
      source.close();
      fetchFallback(query);
    };

    timeoutRef.current = window.setTimeout(() => {
      if (!hasChunk) {
        source.close();
        fetchFallback(query);
      }
    }, 12000);
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
