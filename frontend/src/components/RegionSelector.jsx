import { useEffect, useState } from "react";
import { api } from "../api";

/** Region selector: preset dropdown + custom lat-lon box inputs. */
export default function RegionSelector({ region, setRegion, setRegionLabel }) {
  const [presets, setPresets] = useState([]);
  const [choice, setChoice] = useState("preset");

  useEffect(() => {
    api
      .regions()
      .then((r) => {
        setPresets(r);
        setRegion(r[0].box);
        setRegionLabel(r[0].name);
      })
      .catch(() => {});
  }, []);

  const usePreset = (name) => {
    const p = presets.find((x) => x.name === name);
    if (p) {
      setRegion(p.box);
      setRegionLabel(p.name);
    }
  };

  const update = (k, v) => {
    const next = { ...region, [k]: parseFloat(v) };
    setRegion(next);
    setRegionLabel(
      `Custom box (${next.lat_min}, ${next.lon_min}) to (${next.lat_max}, ${next.lon_max})`
    );
  };

  return (
    <div className="card">
      <h3>Region</h3>
      <div className="row">
        <button className={choice === "preset" ? "active" : ""} onClick={() => setChoice("preset")}>
          Preset city
        </button>
        <button className={choice === "custom" ? "active" : ""} onClick={() => setChoice("custom")}>
          Custom lat-lon box
        </button>
      </div>
      {choice === "preset" ? (
        <select onChange={(e) => usePreset(e.target.value)}>
          {presets.map((p) => (
            <option key={p.name} value={p.name}>
              {p.name}
            </option>
          ))}
        </select>
      ) : (
        <div className="grid2">
          {["lat_min", "lat_max", "lon_min", "lon_max"].map((k) => (
            <label key={k}>
              {k}
              <input
                type="number"
                step="0.1"
                value={region?.[k] ?? ""}
                onChange={(e) => update(k, e.target.value)}
              />
            </label>
          ))}
        </div>
      )}
      {/* Bonus upgrade: replace preset dropdown with a Leaflet map-draw box */}
    </div>
  );
}
