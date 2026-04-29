import { useEffect, useState } from "react";
import { fetchRLDecision, fetchRLStats, fetchAWSActions, fetchOptimizerPreview } from "@/services/api";

const ACTION_ICONS: Record<string, string> = {
  scale_up: "trending_up",
  maintain: "more_horiz",
  scale_down: "trending_down",
};

interface AIOptimizerProps {
  onRunOptimizer: () => void;
}

export default function AIOptimizer({ onRunOptimizer }: AIOptimizerProps) {
  const [decision, setDecision] = useState<any>(null);
  const [stats, setStats] = useState<any>(null);
  const [actions, setActions] = useState<any[]>([]);
  const [preview, setPreview] = useState<any>(null);
  const [mode, setMode] = useState<"Auto" | "Manual">("Auto");

  useEffect(() => {
    load();
  }, []);

  async function load() {
    try {
      const [d, s, a, p] = await Promise.all([
        fetchRLDecision(),
        fetchRLStats(),
        fetchAWSActions(),
        fetchOptimizerPreview(),
      ]);
      setDecision(d.data);
      setStats(s.data);
      setActions(a.data || []);
      setPreview(p.data);
    } catch {}
  }

  const handleApply = () => {
    onRunOptimizer();
  };

  const handlePreview = async () => {
    try {
      const res = await fetchOptimizerPreview();
      setPreview(res.data);
    } catch {}
  };

  const d = decision?.decision;
  const action = d?.action ?? "maintain";
  const explanation = decision?.explanation?.explanation ?? "Loading explanation...";

  const qValues = d?.q_values ? Object.entries(d.q_values) : [];
  const qMin = qValues.length ? Math.min(...qValues.map(([, v]: any) => v)) : 0;
  const qMax = qValues.length ? Math.max(...qValues.map(([, v]: any) => Math.abs(v)), 0.01) : 0.01;

  return (
    <div className="p-10 fade-in">
      <header className="mb-8 flex justify-between items-end">
        <div>
          <h1 className="text-4xl font-extrabold headline text-white tracking-tighter">
            RL Optimizer <span className="text-primary">v2.4</span>
          </h1>
          <p className="text-slate-400 mt-1.5 text-sm max-w-xl">
            Deep Reinforcement Learning engine. 3D state space: CPU × Memory × Requests → 1000 states × 3 actions.
          </p>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 bg-[#191c22] border border-[#3c4a46]/15 rounded-xl">
          <span className="w-2 h-2 rounded-full bg-primary breathing-pulse"></span>
          <span className="text-xs font-semibold text-slate-300 uppercase">System Stable</span>
        </div>
      </header>

      <div className="grid grid-cols-12 gap-6">
        <section className="col-span-5 bg-[#191c22] rounded-xl p-8 border border-[#3c4a46]/10 relative overflow-hidden">
          <div className="absolute -right-16 -top-16 w-64 h-64 bg-primary/5 blur-[100px] rounded-full pointer-events-none"></div>
          <div className="relative z-10">
            <div className="flex items-center justify-between mb-7">
              <h3 className="text-lg font-bold headline text-white">Current Decision</h3>
              <div className="px-3 py-1 bg-primary/20 text-primary rounded-full text-sm font-bold border border-primary/20">
                {d?.epsilon ? `ε=${d.epsilon}` : "—"}
              </div>
            </div>
            <div className="flex items-start gap-5 mb-7">
              <div className="p-4 bg-primary rounded-2xl">
                <span className="material-symbols-outlined text-on-primary text-4xl" style={{ fontVariationSettings: "'FILL' 1" }}>
                  {ACTION_ICONS[action] ?? "more_horiz"}
                </span>
              </div>
              <div>
                <div className="text-4xl font-headline font-extrabold text-primary mb-1">
                  {action.replace("_", " ").toUpperCase()}
                </div>
                <div className="text-sm font-medium text-slate-400">
                  Replicas: <span className="text-white">{d?.replicas ?? "—"}</span>
                </div>
                <div className="text-sm font-medium text-slate-400 mt-1">
                  Reward: <span className="text-primary">{d?.reward ?? "—"}</span>
                </div>
              </div>
            </div>
            <div className="p-5 bg-[#10131a]/50 rounded-xl border border-[#3c4a46]/10 backdrop-blur-md">
              <div className="flex items-center gap-2 mb-3">
                <span className="material-symbols-outlined text-secondary text-sm">auto_awesome</span>
                <span className="text-[10px] font-bold text-slate-300 uppercase tracking-wider">AI Reasoning</span>
              </div>
              <p className="text-sm text-slate-400 leading-relaxed">{explanation}</p>
            </div>
            <div className="mt-5 grid grid-cols-3 gap-3">
              <div className="bg-[#1d2026] p-3 rounded-xl text-center">
                <div className="text-[9px] text-slate-500 uppercase mb-1">CPU Bucket</div>
                <div className="text-lg font-bold headline text-primary">{d?.state?.cpu_bucket ?? "—"}</div>
              </div>
              <div className="bg-[#1d2026] p-3 rounded-xl text-center">
                <div className="text-[9px] text-slate-500 uppercase mb-1">Mem Bucket</div>
                <div className="text-lg font-bold headline text-secondary">{d?.state?.memory_bucket ?? "—"}</div>
              </div>
              <div className="bg-[#1d2026] p-3 rounded-xl text-center">
                <div className="text-[9px] text-slate-500 uppercase mb-1">Req Bucket</div>
                <div className="text-lg font-bold headline text-amber-400">{d?.state?.request_bucket ?? "—"}</div>
              </div>
            </div>
          </div>
        </section>

        <section className="col-span-7 bg-[#191c22] rounded-xl p-8 border border-[#3c4a46]/10 flex flex-col">
          <div className="flex items-center justify-between mb-8">
            <h3 className="text-lg font-bold headline text-white">Q-Values Projection</h3>
            <span className="text-[10px] font-bold text-slate-500 uppercase">Reward per action</span>
          </div>
          <div className="flex-1 flex items-end justify-around gap-6 pb-4" style={{ minHeight: "160px" }}>
            {qValues.length === 0 ? (
              <div className="text-center text-slate-600 text-xs py-8 w-full">Loading Q-values...</div>
            ) : (
              qValues.map(([k, v]: any) => {
                const range = qMax * 2 || 1;
                const h = Math.min(90, Math.max(10, ((v - qMin) / range) * 90 + 10));
                const isActive = k === action;
                return (
                  <div key={k} className="flex-1 group relative flex flex-col items-center">
                    <div className={`text-[10px] font-bold mb-2 ${isActive ? "text-primary" : "text-slate-600"}`}>
                      {v.toFixed(4)}
                    </div>
                    <div
                      className={`w-full rounded-t-xl transition-all duration-700 ${isActive ? "bg-gradient-to-t from-primary/40 to-primary" : "bg-slate-800 hover:bg-slate-700"}`}
                      style={{ height: h + "%" }}
                    ></div>
                    <div className={`mt-3 text-[9px] font-bold uppercase tracking-widest ${isActive ? "text-primary" : "text-slate-500"}`}>
                      {String(k).replace("_", " ")}
                    </div>
                  </div>
                );
              })
            )}
          </div>
          <div className="mt-6 pt-5 border-t border-[#3c4a46]/15">
            <div className="grid grid-cols-4 gap-4 text-center">
              <div>
                <div className="text-[9px] text-slate-500 uppercase mb-1">Q-Table Shape</div>
                <div className="text-sm font-bold headline text-white">{stats?.shape?.join(" × ") ?? "—"}</div>
              </div>
              <div>
                <div className="text-[9px] text-slate-500 uppercase mb-1">Coverage</div>
                <div className="text-sm font-bold headline text-primary">{(stats?.coverage_pct ?? 0) + "%"}</div>
              </div>
              <div>
                <div className="text-[9px] text-slate-500 uppercase mb-1">Max Q-Value</div>
                <div className="text-sm font-bold headline text-white">{stats?.max_q_value?.toFixed(4) ?? "—"}</div>
              </div>
              <div>
                <div className="text-[9px] text-slate-500 uppercase mb-1">Epsilon (ε)</div>
                <div className="text-sm font-bold headline text-secondary">{stats?.epsilon ?? "—"}</div>
              </div>
            </div>
            <div className="mt-4 h-1.5 bg-[#1d2026] rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-primary to-secondary rounded-full transition-all duration-700"
                style={{ width: (stats?.coverage_pct ?? 0) + "%" }}
              ></div>
            </div>
            <div className="text-[10px] text-slate-500 mt-1.5">{stats?.coverage_pct ?? 0}% of state space explored</div>
          </div>
        </section>

        <section className="col-span-4 bg-[#191c22] rounded-xl p-8 border border-[#3c4a46]/10 space-y-5">
          <h3 className="text-base font-bold headline text-white">System Mode</h3>
          <div className="bg-[#10131a] p-1 rounded-full flex w-fit">
            <button
              onClick={() => setMode("Auto")}
              className={`px-4 py-1.5 rounded-full text-xs font-bold transition-colors ${
                mode === "Auto" ? "bg-primary text-on-primary" : "text-slate-500 hover:text-white"
              }`}
            >
              Auto
            </button>
            <button
              onClick={() => setMode("Manual")}
              className={`px-4 py-1.5 rounded-full text-xs font-bold transition-colors ${
                mode === "Manual" ? "bg-primary text-on-primary" : "text-slate-500 hover:text-white"
              }`}
            >
              Manual
            </button>
          </div>

          <button
            onClick={handleApply}
            className="w-full py-4 rounded-xl bg-gradient-to-r from-primary to-primary-container text-on-primary font-bold shadow-[0_8px_32px_rgba(87,241,219,0.2)] hover:opacity-90 transition-all"
          >
            Apply Recommendation
          </button>

          <button
            onClick={handlePreview}
            className="w-full py-4 rounded-xl border border-[#3c4a46] text-slate-300 font-bold hover:bg-white/5 transition-all"
          >
            Preview Impact
          </button>

          {preview && (
            <div className="rounded-xl border border-[#3c4a46]/10 bg-[#10131a]/60 p-4 text-sm text-slate-400">
              <div className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-2">Latest Preview</div>
              <div className="text-white font-semibold">{preview.deployment ?? "load-test-app"}</div>
              <div className="mt-1">
                Recommended replicas: <span className="text-primary font-bold">{preview.recommended_replicas ?? preview.replicas ?? "—"}</span>
              </div>
              <div className="text-[11px] text-slate-500 mt-1">Mode: {preview.mode ?? "preview"}</div>
            </div>
          )}
        </section>

        <section className="col-span-8 bg-[#191c22] rounded-xl p-8 border border-[#3c4a46]/10">
          <div className="flex items-center justify-between mb-7">
            <h3 className="text-lg font-bold headline text-white">Scaling History</h3>
            <span className="text-[10px] font-bold text-slate-500 uppercase">Recent Actions</span>
          </div>
          <div className="space-y-4 relative">
            <div className="absolute left-6 top-2 bottom-2 w-px bg-[#3c4a46]/20"></div>
            {actions.length === 0 ? (
              <div className="text-slate-600 text-xs pl-10">Loading actions...</div>
            ) : (
              actions.slice(0, 8).map((a: any, i: number) => (
                <div key={i} className="relative flex items-center gap-6 pl-4">
                  <div className="relative z-10 w-3 h-3 rounded-full bg-primary ring-4 ring-primary/10 shrink-0"></div>
                  <div className="flex-1 bg-[#1d2026] p-4 rounded-xl flex items-center justify-between border border-[#3c4a46]/5 hover:border-primary/20 transition-all">
                    <div className="flex items-center gap-5">
                      <div>
                        <div className="text-[10px] text-slate-500 font-bold mb-0.5">{new Date(a.timestamp).toLocaleTimeString()}</div>
                        <div className="text-sm font-semibold text-white">{a.action?.replace("_", " ")} · {a.target}</div>
                      </div>
                      <div className="text-xs text-slate-400">
                        {a.previous !== undefined ? `${a.previous} → ${a.new}` : ""}
                      </div>
                    </div>
                    <span
                      className={`px-2 py-0.5 rounded-full text-[9px] font-bold uppercase ${
                        a.action === "scale_up"
                          ? "bg-primary/20 text-primary"
                          : a.action === "scale_down"
                          ? "bg-amber-400/20 text-amber-400"
                          : "bg-slate-700 text-slate-400"
                      }`}
                    >
                      {a.resource_type}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
