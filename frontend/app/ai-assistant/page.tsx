import ChatPanel from "../../components/ChatPanel";

export default function AssistantPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-ink">AI Assistant</h1>
        <p className="text-sm text-muted">
          Get personalized discount and card recommendations powered by Groq.
        </p>
      </div>
      <ChatPanel />
      <div className="rounded-xl border border-border/60 bg-white/5 p-6 text-sm text-muted backdrop-blur">
        Try: "Best food discounts in DHA Karachi" or "Which credit card should I
        use for dining?"
      </div>
    </div>
  );
}
