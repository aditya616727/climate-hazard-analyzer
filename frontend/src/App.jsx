import { useState } from "react";
import { api } from "./api";
import RegionSelector from "./components/RegionSelector";
import TrendChart from "./components/TrendChart";
import InsightPanel from "./components/InsightPanel";
import AiChat from "./components/AiChat";

export default function App() {
  const [region, setRegion] = useState(null);
  const [regionLabel, setRegionLabel] = useState("");
  const [startYear, setStartYear] = useState(1990);
  const [endYear, setEndYear] = useState(2020);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const run = async () => {
    if (!region) return;
    setLoading(true);
    setError("");
    try {
      const r = await api.analyze(region, startYear, endYear);
      setAnalysis(r);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header>
        <h1>Climate Hazard Trend Analyzer</h1>
        <p className="muted">Heatwave trends from ERA5 reanalysis data (Open-Meteo)</p>
      </header>

      <RegionSelector region={region} setRegion={setRegion} setRegionLabel={setRegionLabel} />

      <div className="card">
        <h3>Time range & hazard</h3>
        <div className="row">
          <label>
            Start year
            <input type="number" value={startYear} onChange={(e) => setStartYear(+e.target.value)} />
          </label>
          <label>
            End year
            <input type="number" value={endYear} onChange={(e) => setEndYear(+e.target.value)} />
          </label>
          <label>
            Hazard
            <select disabled>
              <option>heatwave</option>
            </select>
          </label>
        </div>
        <button onClick={run} disabled={loading || !region}>
          {loading ? "Analyzing..." : "Analyze"}
        </button>
        {error && <p className="error">{error}</p>}
      </div>

      {analysis && (
        <>
          <div className="headline">{analysis.headline}</div>
          <TrendChart analysis={analysis} />
          <InsightPanel analysis={analysis} regionLabel={regionLabel} />
          <AiChat analysis={analysis} />
          <div className="card">
            <button onClick={() => api.exportCsv(analysis)}>Download CSV</button>
          </div>
        </>
      )}
    </div>
  );
}
