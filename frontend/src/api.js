const BASE = import.meta.env.VITE_API_URL || "";

async function post(path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    let msg = `API error ${res.status}`;
    try {
      const data = await res.json();
      msg = data.detail || msg;
    } catch {
      const text = await res.text();
      msg += `: ${text}`;
    }
    throw new Error(msg);
  }
  return res.json();
}

export const api = {
  analyze: (region, startYear, endYear) =>
    post("/api/analyze", {
      region,
      start_year: startYear,
      end_year: endYear,
      hazard: "heatwave",
    }),
  aiInsight: (analysis, regionLabel) =>
    post("/api/ai/insight", { analysis, region_label: regionLabel }),
  aiAsk: (analysis, question) => post("/api/ai/ask", { analysis, question }),
  regions: () => fetch(`${BASE}/api/regions`).then((r) => r.json()),
  exportCsv: async (analysis) => {
    const res = await fetch(`${BASE}/api/export/csv`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ analysis, region_label: "" }),
    });
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "heatwave_analysis.csv";
    a.click();
    URL.revokeObjectURL(url);
  },
};
