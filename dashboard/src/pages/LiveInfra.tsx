import { useEffect, useState, useRef } from "react";
import { fetchMetrics } from "@/services/api";
import Chart from "chart.js/auto";
import { makeGradient } from "@/lib/chartUtils";

export default function LiveInfra() {
  const [cpu, setCpu] = useState("—");
  const [mem, setMem] = useState("—");
  const [req, setReq] = useState("—");
  const [cpuPct, setCpuPct] = useState(0);
  const [memPct, setMemPct] = useState(0);
  const chartRef = useRef<HTMLCanvasElement | null>(null);
  const chartInstance = useRef<any>(null);

  useEffect(() => {
    load();
    const interval = setInterval(load, 15000);
    return () => clearInterval(interval);
  }, []);

  async function load() {
    try {
      const res = await fetchMetrics();
      const metrics = res.data;
      if (!metrics?.length) return;

      const latest = metrics[0];
      const cpuVal = Math.max(0, latest.cpu_usage);
      const memVal = latest.memory_usage;
      const reqVal = latest.request_load;

      setCpu(cpuVal.toFixed(1) + "%");
      setMem(memVal.toFixed(1) + "%");
      setReq(reqVal.toFixed(4));
      setCpuPct(Math.min(100, cpuVal));
      setMemPct(Math.min(100, memVal));

      const recent = metrics.slice(0, 30).reverse();
      const labels = recent.map((m: any) =>
        new Date(m.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
      );

      if (chartRef.current) {
        const ctx = chartRef.current.getContext("2d")!;
        if (chartInstance.current) chartInstance.current.destroy();
        chartInstance.current = new Chart(ctx, {
          type: "line",
          data: {
            labels,
            datasets: [
              { label: "CPU", data: recent.map((m: any) => Math.max(0, m.cpu_usage)), borderColor: "#57f1db", fill: true, backgroundColor: makeGradient(ctx, "#57f1db"), tension: 0.4, pointRadius: 0, borderWidth: 2 },
              { label: "Memory", data: recent.map((m: any) => m.memory_usage), borderColor: "#d0bcff", fill: true, backgroundColor: makeGradient(ctx, "#d0bcff"), tension: 0.4, pointRadius: 0, borderWidth: 2 }
            ]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: "index", intersect: false },
            plugins: {
              legend: { labels: { color: "#6b7280" } },
              tooltip: { backgroundColor: "#1d2026", borderColor: "rgba(87,241,219,0.2)", borderWidth: 1 }
            },
            scales: {
              x: { grid: { color: "rgba(87,241,219,0.04)" } },
              y: { grid: { color: "rgba(87,241,219,0.04)" }, ticks: { callback: (v: any) => v + "%" } }
            }
          }
        });
      }
    } catch {}
  }

  return (
    <div className="p-10 fade-in">
      <header className="mb-8">
        <h1 className="text-4xl font-extrabold headline text-white tracking-tighter">Live Infrastructure</h1>
        <p className="text-slate-400 mt-1.5 text-sm">Real-time Prometheus metrics from your cluster</p>
      </header>

      <div className="grid grid-cols-3 gap-5 mb-8">
        <div className="glass-panel p-6 rounded-xl">
          <div className="text-[9px] font-bold text-slate-500 uppercase tracking-widest mb-3">CPU Utilization</div>
          <div className="text-5xl font-extrabold headline text-primary mb-2">{cpu}</div>
          <div className="h-1.5 bg-[#1d2026] rounded-full overflow-hidden">
            <div className="h-full bg-primary rounded-full transition-all duration-700" style={{ width: cpuPct + "%" }}></div>
          </div>
        </div>

        <div className="glass-panel p-6 rounded-xl">
          <div className="text-[9px] font-bold text-slate-500 uppercase tracking-widest mb-3">Memory Usage</div>
          <div className="text-5xl font-extrabold headline text-secondary mb-2">{mem}</div>
          <div className="h-1.5 bg-[#1d2026] rounded-full overflow-hidden">
            <div className="h-full bg-secondary rounded-full transition-all duration-700" style={{ width: memPct + "%" }}></div>
          </div>
        </div>

        <div className="glass-panel p-6 rounded-xl">
          <div className="text-[9px] font-bold text-slate-500 uppercase tracking-widest mb-3">Request Load</div>
          <div className="text-5xl font-extrabold headline text-amber-400 mb-2">{req}</div>
          <div className="text-xs text-slate-500">req/s</div>
        </div>
      </div>

      <div className="glass-panel p-7 rounded-xl min-h-[400px] flex flex-col">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-lg font-bold headline text-white">Telemetry Timeline</h3>
          <div className="flex items-center gap-2 text-[10px] font-bold text-primary uppercase">
            <span className="w-1.5 h-1.5 rounded-full bg-primary breathing-pulse"></span>
            Live · 15s refresh
          </div>
        </div>
        <div className="flex-1">
          <canvas ref={chartRef}></canvas>
        </div>
      </div>
    </div>
  );
}