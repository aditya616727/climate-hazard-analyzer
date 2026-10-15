import { useState } from "react";
import { api } from "../api";

/** AI-generated plain-language briefing (falls back to template without an API key). */
export default function InsightPanel({ analysis, regionLabel }) {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);

  const generate = async () => {
    setLoading(true);
    try {
      const r = await api.aiInsight(analysis, regionLabel);
      setText(r.narrative);
    } catch (e) {
      setText(`Could not generate AI insight: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h3>AI Insight</h3>
      <button onClick={generate} disabled={loading}>
        {loading ? "Generating..." : "Explain these results"}
      </button>
      {text && <p className="insight">{text}</p>}
    </div>
  );
}
