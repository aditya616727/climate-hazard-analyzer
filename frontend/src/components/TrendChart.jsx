import {
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Title,
  Tooltip,
} from "chart.js";
import { Line } from "react-chartjs-2";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

export default function TrendChart({ analysis }) {
  const labels = analysis.yearly.map((y) => y.year);
  const data = {
    labels,
    datasets: [
      {
        label: "Heatwave events / year",
        data: analysis.yearly.map((y) => y.heatwave_count),
        borderColor: "#e4572e",
        backgroundColor: "rgba(228,87,46,0.2)",
        tension: 0.3,
      },
      {
        label: "Heatwave days / year",
        data: analysis.yearly.map((y) => y.heatwave_days),
        borderColor: "#f3a712",
        backgroundColor: "rgba(243,167,18,0.2)",
        tension: 0.3,
      },
    ],
  };
  return (
    <div className="card">
      <h3>Heatwave frequency over time</h3>
      <p className="muted">
        Threshold: {analysis.threshold_c}°C (95th percentile of baseline).{" "}
        {analysis.headline}
      </p>
      <Line data={data} options={{ responsive: true, plugins: { legend: { position: "top" } } }} />
    </div>
  );
}
