import { useState } from "react";
import { api } from "../api";

/** Grounded Q&A: ask anything about the analysis; answers come only from verified stats. */
export default function AiChat({ analysis }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const ask = async () => {
    const q = input.trim();
    if (!q || loading) return;
    setMessages((m) => [...m, { role: "user", text: q }]);
    setInput("");
    setLoading(true);
    try {
      const r = await api.aiAsk(analysis, q);
      setMessages((m) => [...m, { role: "ai", text: r.answer }]);
    } catch (e) {
      setMessages((m) => [...m, { role: "ai", text: `Error: ${e.message}` }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h3>Ask the data</h3>
      <div className="chat">
        {messages.map((m, i) => (
          <div key={i} className={`msg ${m.role}`}>
            {m.text}
          </div>
        ))}
        {!messages.length && (
          <p className="muted">Try: “Which year had the longest heatwave?”</p>
        )}
      </div>
      <div className="row">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && ask()}
          placeholder="Ask about the trend..."
        />
        <button onClick={ask} disabled={loading}>
          Ask
        </button>
      </div>
    </div>
  );
}
