import { useEffect, useState } from "react";
import { fetchCostForecast } from "@/services/api";

export default function Intelligence() {
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    fetchCostForecast()
      .then((res) => setData(res.data))
      .catch(() => {});
  }, []);

  function fmtTime(t: string) {
    try { return new Date(t).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }); } catch { return t; }
  }

  return (
    <div className="p-10 fade-in">
      <header className="mb-8">
        <h1 className="text-4xl font-extrabold headline text-white tracking-tighter">Cost Intelligence</h1>
        <p className="text-slate-400 mt-1.5 text-sm">Prophet ML forecast · 30-day lookahead</p>
      </header>

      <div className="grid grid-cols-3 gap-5 mb-8">
        <div className="glass-panel p-6 rounded-xl">
          <div className="text-[9px] font-bold text-slate-500 uppercase tracking-widest mb-3">Predicted CPU (next)</div>
          <div className="text-4xl font-extrabold headline text-primary">{data ? data.predicted_cpu?.toFixed(1) + "%" : "—"}</div>
        </div>
        <div className="glass-panel p-6 rounded-xl">
          <div className="text-[9px] font-bold text-slate-500 uppercase tracking-widest mb-3">Predicted Memory (next)</div>
          <div className="text-4xl font-extrabold headline text-secondary">{data ? data.predicted_memory?.toFixed(1) + "%" : "—"}</div>
        </div>
        <div className="glass-panel p-6 rounded-xl border-primary/20 bg-primary/5">
          <div className="text-[9px] font-bold text-primary uppercase tracking-widest mb-3">Hourly Cost Forecast</div>
          <div className="text-4xl font-extrabold headline text-primary">{data ? "$" + data.predicted_hourly_cost?.toFixed(4) : "—"}</div>
          <div className="text-xs text-white mt-2">{data ? data.required_instances + " required instances" : "— required instances"}</div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="glass-panel p-7 rounded-xl">
          <h3 className="text-base font-bold headline text-white mb-5">CPU Forecast (6 steps)</h3>
          <div className="space-y-3">
            {data?.cpu_forecast ? data.cpu_forecast.map((p: any, i: number) => (
              <div key={i} className="flex items-center gap-3">
                <span className="text-[10px] font-mono text-slate-500 w-14">{fmtTime(p.timestamp)}</span>
                <div className="flex-1 h-1.5 bg-[#1d2026] rounded-full overflow-hidden">
                  <div className="h-full bg-primary rounded-full" style={{ width: Math.min(100, Math.max(0, p.prediction)) + "%" }}></div>
                </div>
                <span className="text-xs font-bold text-primary w-14 text-right">{p.prediction.toFixed(1)}%</span>
              </div>
            )) : <div className="text-slate-600 text-xs">Loading...</div>}
          </div>
        </div>

        <div className="glass-panel p-7 rounded-xl">
          <h3 className="text-base font-bold headline text-white mb-5">Request Load Forecast</h3>
          <div className="space-y-3">
            {data?.request_forecast ? data.request_forecast.map((p: any, i: number) => (
              <div key={i} className="flex items-center gap-3">
                <span className="text-[10px] font-mono text-slate-500 w-14">{fmtTime(p.timestamp)}</span>
                <div className="flex-1 h-1.5 bg-[#1d2026] rounded-full overflow-hidden">
                  <div className="h-full bg-secondary rounded-full" style={{ width: Math.min(100, p.prediction * 50) + "%" }}></div>
                </div>
                <span className="text-xs font-bold text-secondary w-16 text-right">{p.prediction.toFixed(4)}</span>
              </div>
            )) : <div className="text-slate-600 text-xs">Loading...</div>}
          </div>
        </div>
      </div>
    </div>
  );
}