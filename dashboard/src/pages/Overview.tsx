import { useEffect, useState, useRef } from "react";
import {
  fetchMetrics,
  fetchRLDecision,
  fetchAzureCost,
  fetchCostForecast,
  fetchRLStats,
  fetchAWSState
} from "@/services/api";
import Chart from "chart.js/auto";
import { makeGradient } from "@/lib/chartUtils";

interface OverviewProps {
  onNavigate: (page: string) => void;
  onRunOptimizer: () => void;
}

export default function Overview({ onNavigate, onRunOptimizer }: OverviewProps) {
  const chartRef = useRef<HTMLCanvasElement | null>(null);
  const chartInstance = useRef<any>(null);
  const [lastUpdated, setLastUpdated] = useState("");

  const [kpis, setKpis] = useState({
    azureCost: "—",
    azureCredits: "loading...",
    creditsPositive: true,
    cpu: "—",
    cpuSub: "from Prometheus",
    mem: "—",
    action: "—",
    replicas: "—",
    reward: "—",
    epsilon: "—",
    aiExplanation: "Fetching latest RL agent decision...",
    aiActionTitle: "Loading...",
    coverage: 0,
    forecast: "—",
    forecastSub: "Prophet model",
    decisionTime: "—",
  });

  const [awsRows, setAwsRows] = useState<any[]>([]);

  useEffect(() => {
    load();
    const interval = setInterval(load, 15000);
    return () => clearInterval(interval);
  }, []);

  async function load() {
    const [m, decision, azure, awsState, forecast, rlStats] = await Promise.all([
      fetchMetrics().catch(() => ({ data: null })),
      fetchRLDecision().catch(() => ({ data: null })),
      fetchAzureCost().catch(() => ({ data: null })),
      fetchAWSState().catch(() => ({ data: null })),
      fetchCostForecast().catch(() => ({ data: null })),
      fetchRLStats().catch(() => ({ data: null })),
    ]);

    const metrics = m.data;
    const d = decision.data;
    const az = azure.data;
    const fc = forecast.data;
    const stats = rlStats.data;
    const aws = awsState.data;

    setKpis((prev) => {
      const next = { ...prev };

      if (az) {
        next.azureCost = "$" + az.amount?.toFixed(2);
        const rem = (100 - az.amount).toFixed(2);
        next.creditsPositive = parseFloat(rem) > 0;
        next.azureCredits = parseFloat(rem) > 0 ? `$${rem} credits left` : `Over budget by $${Math.abs(parseFloat(rem))}`;
      }

      if (metrics?.length) {
        const last = metrics[metrics.length - 1];
        next.cpu = last.cpu_usage.toFixed(1) + "%";
        next.cpuSub = `memory: ${last.memory_usage.toFixed(1)}%`;
        next.mem = last.memory_usage.toFixed(1) + "%";
      }

      if (d?.decision) {
        const dec = d.decision;
        const action = dec.action?.replace("_", " ").toUpperCase() ?? "—";
        next.action = action;
        next.aiActionTitle = action;
        next.replicas = dec.replicas ?? "—";
        next.reward = dec.reward ?? "—";
        next.epsilon = dec.epsilon ?? "—";
        next.decisionTime = new Date().toLocaleTimeString();
      }

      if (d?.explanation?.explanation) {
        next.aiExplanation = d.explanation.explanation;
      }

      if (fc) {
        next.forecast = "$" + (fc.predicted_hourly_cost ?? 0).toFixed(4);
        next.forecastSub = `CPU forecast: ${(fc.predicted_cpu ?? 0).toFixed(1)}%`;
      }

      if (stats) {
        next.coverage = stats.coverage_pct ?? 0;
      }

      return next;
    });

    // AWS rows
    if (aws) {
      const rows: any[] = [];
      (aws.asgs ?? []).forEach((a: any) => rows.push({ type: "ASG", name: a.name, status: "Active", desired: a.desired, max: a.max, color: "primary" }));
      Object.entries(aws.ecs ?? {}).forEach(([cluster, svcs]: any) => {
        (svcs as any[]).forEach((s: any) => rows.push({ type: "ECS", name: cluster, status: s.status, desired: s.desired, max: Math.max(s.desired, 1), running: s.running, color: "secondary" }));
      });
      setAwsRows(rows);
    }

    // Chart
    if (metrics?.length) {
      const labels = metrics.slice(-20).map((m: any) =>
        new Date(m.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
      );
      const cpuData = metrics.slice(-20).map((m: any) => Math.max(0, m.cpu_usage));
      const memData = metrics.slice(-20).map((m: any) => m.memory_usage);

      if (chartRef.current) {
        const ctx = chartRef.current.getContext("2d")!;
        if (chartInstance.current) chartInstance.current.destroy();
        chartInstance.current = new Chart(ctx, {
          type: "line",
          data: {
            labels,
            datasets: [
              { label: "CPU %", data: cpuData, borderColor: "#57f1db", fill: true, backgroundColor: makeGradient(ctx, "#57f1db"), tension: 0.4, pointRadius: 0, borderWidth: 2 },
              { label: "Memory %", data: memData, borderColor: "#d0bcff", fill: true, backgroundColor: makeGradient(ctx, "#d0bcff"), tension: 0.4, pointRadius: 0, borderWidth: 2 }
            ]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: "index", intersect: false },
            plugins: {
              legend: { display: false },
              tooltip: { backgroundColor: "#1d2026", borderColor: "rgba(87,241,219,0.2)", borderWidth: 1 }
            },
            scales: {
              x: { grid: { color: "rgba(87,241,219,0.04)" }, ticks: { maxTicksLimit: 8 } },
              y: { grid: { color: "rgba(87,241,219,0.04)" }, ticks: { callback: (v: any) => v + "%" } }
            }
          }
        });
      }
    }

    setLastUpdated("Updated " + new Date().toLocaleTimeString());
  }

  return (
    <div className="p-10 fade-in">
      {/* Header */}
      <header className="mb-8 flex justify-between items-end">
        <div>
          <h1 className="text-4xl font-extrabold headline text-white tracking-tighter">Command Center</h1>
          <p className="text-slate-400 mt-1.5 text-sm">Global infrastructure spend & AI optimization metrics</p>
        </div>
        <div className="text-[10px] font-mono text-slate-600 uppercase">{lastUpdated}</div>
      </header>

      {/* KPI Row */}
      <div className="grid grid-cols-5 gap-5 mb-8">
        <div className="glass-panel p-5 rounded-xl hover:bg-[#272a31]/30 transition-all">
          <div className="flex justify-between items-start mb-4">
            <span className="text-slate-500 font-bold text-[9px] uppercase tracking-widest">Azure Cost MTD</span>
            <span className="material-symbols-outlined text-primary text-lg">payments</span>
          </div>
          <div className="text-3xl font-bold headline text-white">{kpis.azureCost}</div>
          <div className={`text-[11px] mt-2 flex items-center gap-1 ${kpis.creditsPositive ? "text-primary" : "text-red-400"}`}>
            <span className="material-symbols-outlined text-xs">account_balance_wallet</span>
            {kpis.azureCredits}
          </div>
        </div>

        <div className="glass-panel p-5 rounded-xl hover:bg-[#272a31]/30 transition-all">
          <div className="flex justify-between items-start mb-4">
            <span className="text-slate-500 font-bold text-[9px] uppercase tracking-widest">Live CPU</span>
            <span className="material-symbols-outlined text-secondary text-lg">memory</span>
          </div>
          <div className="text-3xl font-bold headline text-white">{kpis.cpu}</div>
          <div className="text-[11px] text-slate-500 mt-2">{kpis.cpuSub}</div>
        </div>

        <div className="glass-panel p-5 rounded-xl hover:bg-[#272a31]/30 transition-all">
          <div className="flex justify-between items-start mb-4">
            <span className="text-slate-500 font-bold text-[9px] uppercase tracking-widest">Memory Usage</span>
            <span className="material-symbols-outlined text-slate-400 text-lg">storage</span>
          </div>
          <div className="text-3xl font-bold headline text-white">{kpis.mem}</div>
          <div className="text-[11px] text-slate-500 mt-2">real-time</div>
        </div>

        <div className="glass-panel p-5 rounded-xl border-primary/20 bg-primary/5 hover:bg-primary/10 transition-all">
          <div className="flex justify-between items-start mb-4">
            <span className="text-primary font-bold text-[9px] uppercase tracking-widest">RL Decision</span>
            <span className="material-symbols-outlined text-primary text-lg" style={{ fontVariationSettings: "'FILL' 1" }}>bolt</span>
          </div>
          <div className="text-3xl font-bold headline text-primary">{kpis.action}</div>
          <div className="text-[11px] text-white mt-2 flex items-center gap-1">
            <span className="material-symbols-outlined text-xs">dynamic_feed</span>
            {kpis.replicas} replicas
          </div>
        </div>

        <div className="glass-panel p-5 rounded-xl hover:bg-[#272a31]/30 transition-all">
          <div className="flex justify-between items-start mb-4">
            <span className="text-slate-500 font-bold text-[9px] uppercase tracking-widest">Forecast Cost/h</span>
            <span className="material-symbols-outlined text-emerald-400 text-lg">trending_up</span>
          </div>
          <div className="text-3xl font-bold headline text-white">{kpis.forecast}</div>
          <div className="text-[11px] text-slate-500 mt-2">{kpis.forecastSub}</div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-12 gap-6 mb-8">
        <div className="col-span-8 glass-panel p-7 rounded-xl flex flex-col min-h-[380px]">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h3 className="text-lg font-bold headline text-white">Cost vs. Load Correlation</h3>
              <p className="text-xs text-slate-400 mt-1">Real-time CPU & memory from Prometheus</p>
            </div>
            <div className="flex gap-2">
              <span className="flex items-center gap-1.5 text-[10px] text-slate-500">
                <span className="w-3 h-0.5 bg-primary inline-block rounded"></span>CPU
              </span>
              <span className="flex items-center gap-1.5 text-[10px] text-slate-500 ml-3">
                <span className="w-3 h-0.5 bg-secondary inline-block rounded"></span>Memory
              </span>
            </div>
          </div>
          <div className="flex-1">
            <canvas ref={chartRef}></canvas>
          </div>
        </div>

        <div className="col-span-4 glass-panel p-7 rounded-xl border-primary/30 bg-gradient-to-br from-primary/5 to-transparent relative overflow-hidden flex flex-col">
          <div className="absolute -right-10 -top-10 w-40 h-40 bg-primary/10 rounded-full blur-3xl pointer-events-none"></div>
          <div className="flex items-center gap-2 mb-5">
            <span className="material-symbols-outlined text-primary" style={{ fontVariationSettings: "'FILL' 1" }}>psychology</span>
            <h3 className="text-base font-bold headline text-white">AI Optimization</h3>
          </div>
          <div className="bg-[#32353c] p-4 rounded-xl border border-primary/20 mb-5">
            <div className="flex justify-between items-start mb-2">
              <span className="px-2 py-0.5 bg-primary/20 text-primary rounded text-[9px] font-bold uppercase">Live Decision</span>
              <span className="text-slate-500 text-[10px]">{kpis.decisionTime}</span>
            </div>
            <div className="text-white font-bold mb-1 text-sm">{kpis.aiActionTitle}</div>
            <p className="text-[11px] text-slate-400 leading-relaxed">{kpis.aiExplanation}</p>
          </div>
          <div className="space-y-3 mb-6">
            <div className="flex justify-between text-sm">
              <span className="text-slate-400">Reward Score</span>
              <span className="text-primary font-bold">{kpis.reward}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-slate-400">Exploration (ε)</span>
              <span className="text-white font-bold">{kpis.epsilon}</span>
            </div>
            <div className="w-full bg-[#1d2026] h-1 rounded-full overflow-hidden">
              <div className="bg-primary h-full transition-all duration-700" style={{ width: kpis.coverage + "%" }}></div>
            </div>
            <div className="text-[10px] text-slate-500">{kpis.coverage}% state space explored</div>
          </div>
          <button
            onClick={onRunOptimizer}
            className="w-full py-3.5 rounded-full bg-primary text-on-primary font-extrabold text-sm shadow-[0_4px_24px_rgba(87,241,219,0.3)] hover:scale-[1.02] active:scale-[0.98] transition-all"
          >
            Execute Optimization
          </button>
        </div>
      </div>

      {/* Infrastructure Table */}
      <div className="glass-panel rounded-xl overflow-hidden">
        <div className="p-5 border-b border-[#3c4a46]/15 flex justify-between items-center bg-[#191c22]/50">
          <h3 className="font-bold headline text-white">AWS Resources (Mock)</h3>
          <button
            onClick={() => onNavigate("resources")}
            className="text-xs text-slate-400 hover:text-primary transition-colors flex items-center gap-1"
          >
            View Full Inventory <span className="material-symbols-outlined text-xs">arrow_forward</span>
          </button>
        </div>
        <div className="p-5">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="text-slate-500 font-bold uppercase text-[9px] tracking-widest border-b border-[#3c4a46]/15">
                <th className="pb-3">Resource</th>
                <th className="pb-3">Type</th>
                <th className="pb-3">Status</th>
                <th className="pb-3">Capacity</th>
                <th className="pb-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="text-on-surface">
              {awsRows.length === 0 ? (
                <tr><td colSpan={5} className="py-6 text-center text-slate-600 text-xs">Loading resources...</td></tr>
              ) : (
                awsRows.map((row, i) => (
                  <tr key={i} className="group hover:bg-[#272a31]/30 transition-all border-b border-[#3c4a46]/5">
                    <td className="py-3 font-medium flex items-center gap-2">
                      <div className={`w-1.5 h-1.5 rounded-full ${row.color === "primary" ? "bg-primary" : "bg-secondary"}`}></div>
                      {row.name}
                    </td>
                    <td className="py-3 text-[10px] text-slate-400 uppercase">{row.type}</td>
                    <td className="py-3">
                      <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold ${row.color === "primary" ? "bg-emerald-400/10 text-emerald-400" : "bg-secondary/10 text-secondary"}`}>
                        {row.status}
                      </span>
                    </td>
                    <td className="py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-20 bg-[#1d2026] h-1 rounded-full overflow-hidden">
                          <div
                            className={`h-full ${row.color === "primary" ? "bg-primary" : "bg-secondary"}`}
                            style={{ width: Math.round((row.desired / row.max) * 100) + "%" }}
                          ></div>
                        </div>
                        <span className="text-xs text-slate-400">{row.desired}/{row.max}</span>
                      </div>
                    </td>
                    <td className="py-3 text-right">
                      <span className="material-symbols-outlined text-slate-500 cursor-pointer hover:text-white text-sm">more_vert</span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}