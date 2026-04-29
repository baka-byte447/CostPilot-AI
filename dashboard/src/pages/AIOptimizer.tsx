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
          <h1 className="text-4xl font-extrabold headline text-text tracking-tighter">
            RL Optimizer <span className="text-primary">v2.4</span>
          </h1>
          <p className="text-textMuted mt-1.5 text-sm max-w-xl">
            Deep Reinforcement Learning engine. 3D state space: CPU × Memory × Requests → 1000 states × 3 actions.
          </p>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 glass-pill">
          <span className="w-2 h-2 rounded-full bg-primary breathing-pulse"></span>
          <span className="text-xs font-semibold text-textMuted uppercase tracking-widest">System Stable</span>
        </div>
      </header>

      <div className="grid grid-cols-12 gap-6">
        <section className="col-span-5 glass-card p-8 relative overflow-hidden">
          <div className="absolute -right-16 -top-16 w-64 h-64 bg-primary/5 blur-[100px] rounded-full pointer-events-none"></div>
          <div className="relative z-10">
            <div className="flex items-center justify-between mb-7">
              <h3 className="text-lg font-bold headline text-text">Current Decision</h3>
              <div className="px-3 py-1 rounded-full border border-primary/40 bg-primary/15 text-primary text-xs font-bold">
                {d?.epsilon ? `ε=${d.epsilon}` : "—"}
              </div>
            </div>
            <div className="flex items-start gap-5 mb-7">
              <div className="p-4 rounded-2xl border border-primary/30 bg-primary/15">
                <span className="material-symbols-outlined text-on-primary text-4xl" style={{ fontVariationSettings: "'FILL' 1" }}>
                  {ACTION_ICONS[action] ?? "more_horiz"}
                </span>
              </div>
              <div>
                <div className="text-4xl font-headline font-extrabold text-primary mb-1">
                  {action.replace("_", " ").toUpperCase()}
                </div>
                <div className="text-sm font-medium text-textMuted">
                  Replicas: <span className="text-text">{d?.replicas ?? "—"}</span>
                </div>
                <div className="text-sm font-medium text-textMuted mt-1">
                  Reward: <span className="text-primary">{d?.reward ?? "—"}</span>
                </div>
              </div>
            </div>
            <div className="p-5 glass-inset">
              <div className="flex items-center gap-2 mb-3">
                <span className="material-symbols-outlined text-primary text-sm">auto_awesome</span>
                <span className="text-[10px] font-bold text-primary uppercase tracking-wider">AI Reasoning</span>
              </div>
              <p className="text-sm text-textMuted leading-relaxed">{explanation}</p>
            </div>
            <div className="mt-5 grid grid-cols-3 gap-3">
              <div className="glass-pill p-3 text-center">
                <div className="text-[9px] text-textMuted uppercase mb-1">CPU Bucket</div>
                <div className="text-lg font-bold headline text-primary">{d?.state?.cpu_bucket ?? "—"}</div>
              </div>
              <div className="glass-pill p-3 text-center">
                <div className="text-[9px] text-textMuted uppercase mb-1">Mem Bucket</div>
                <div className="text-lg font-bold headline text-primary">{d?.state?.memory_bucket ?? "—"}</div>
              </div>
              <div className="glass-pill p-3 text-center">
                <div className="text-[9px] text-textMuted uppercase mb-1">Req Bucket</div>
                <div className="text-lg font-bold headline text-primary">{d?.state?.request_bucket ?? "—"}</div>
              </div>
            </div>
          </div>
        </section>

        <section className="col-span-7 glass-card p-8 flex flex-col">
          <div className="flex items-center justify-between mb-8">
            <h3 className="text-lg font-bold headline text-text">Q-Values Projection</h3>
            <span className="text-[10px] font-bold text-textDim uppercase">Reward per action</span>
          </div>
          <div className="flex-1 glass-inset flex items-end justify-around gap-6 px-4 pb-4 pt-4" style={{ minHeight: "160px" }}>
            {qValues.length === 0 ? (
              <div className="text-center text-textMuted text-xs py-8 w-full">Loading Q-values...</div>
            ) : (
              qValues.map(([k, v]: any) => {
                const range = qMax * 2 || 1;
                const h = Math.min(90, Math.max(10, ((v - qMin) / range) * 90 + 10));
                const isActive = k === action;
                return (
                  <div key={k} className="flex-1 group relative flex flex-col items-center">
                    <div className={`text-[10px] font-bold mb-2 ${isActive ? "text-primary" : "text-textMuted"}`}>
                      {v.toFixed(4)}
                    </div>
                    <div
                      className={`w-full rounded-t-xl transition-all duration-700 ${isActive ? "bg-gradient-to-t from-primary/40 to-primary" : "bg-[rgba(57,62,65,0.55)] hover:bg-[rgba(57,62,65,0.7)]"}`}
                      style={{ height: h + "%" }}
                    ></div>
                    <div className={`mt-3 text-[9px] font-bold uppercase tracking-widest ${isActive ? "text-primary" : "text-textDim"}`}>
                      {String(k).replace("_", " ")}
                    </div>
                  </div>
                );
              })
            )}
          </div>
          <div className="mt-6 pt-5 border-t border-[rgba(246,247,235,0.12)]">
            <div className="grid grid-cols-4 gap-4 text-center">
              <div>
                <div className="text-[9px] text-textMuted uppercase mb-1">Q-Table Shape</div>
                <div className="text-sm font-bold headline text-text">{stats?.shape?.join(" × ") ?? "—"}</div>
              </div>
              <div>
                <div className="text-[9px] text-textMuted uppercase mb-1">Coverage</div>
                <div className="text-sm font-bold headline">
                  <span className="inline-flex items-center rounded-full border border-primary/40 bg-primary/15 px-2 py-0.5 text-[10px] font-bold text-primary">
                    {(stats?.coverage_pct ?? 0) + "%"}
                  </span>
                </div>
              </div>
              <div>
                <div className="text-[9px] text-textMuted uppercase mb-1">Max Q-Value</div>
                <div className="text-sm font-bold headline text-text">{stats?.max_q_value?.toFixed(4) ?? "—"}</div>
              </div>
              <div>
                <div className="text-[9px] text-textMuted uppercase mb-1">Epsilon (ε)</div>
                <div className="text-sm font-bold headline text-text">{stats?.epsilon ?? "—"}</div>
              </div>
            </div>
            <div className="mt-4 h-1.5 bg-surfaceBorder rounded-full overflow-hidden">
              <div
                className="h-full bg-primary rounded-full transition-all duration-700"
                style={{ width: (stats?.coverage_pct ?? 0) + "%" }}
              ></div>
            </div>
            <div className="text-[10px] text-textMuted mt-1.5">{stats?.coverage_pct ?? 0}% of state space explored</div>
          </div>
        </section>

        <section className="col-span-4 glass-card p-8 space-y-5">
          <h3 className="text-base font-bold headline text-text">System Mode</h3>
          <div className="glass-pill p-1 flex w-fit">
            <button
              onClick={() => setMode("Auto")}
              className={`px-4 py-1.5 rounded-full text-xs font-bold transition-all ${
                mode === "Auto"
                  ? "bg-primary text-on-primary shadow-[0_0_12px_rgba(233,79,55,0.25)]"
                  : "ghost-pill hover:text-text"
              }`}
            >
              Auto
            </button>
            <button
              onClick={() => setMode("Manual")}
              className={`px-4 py-1.5 rounded-full text-xs font-bold transition-all ${
                mode === "Manual"
                  ? "bg-primary text-on-primary shadow-[0_0_12px_rgba(233,79,55,0.25)]"
                  : "ghost-pill hover:text-text"
              }`}
            >
              Manual
            </button>
          </div>

          <button
            onClick={handleApply}
            className="w-full py-4 rounded-xl cta-button cta-glow font-bold"
          >
            Apply Recommendation
          </button>

          <button
            onClick={handlePreview}
            className="w-full py-4 rounded-xl ghost-button font-bold"
          >
            Simulate Impact
          </button>

          {preview && (
            <div className="glass-inset p-4 text-sm text-textMuted">
              <div className="text-[10px] font-bold uppercase tracking-widest text-textDim mb-2">Latest Preview</div>
              <div className="text-text font-semibold">{preview.deployment ?? "load-test-app"}</div>
              <div className="mt-1">
                Recommended replicas: <span className="text-primary font-bold">{preview.recommended_replicas ?? preview.replicas ?? "—"}</span>
              </div>
              <div className="text-[11px] text-textDim mt-1">Mode: {preview.mode ?? "preview"}</div>
            </div>
          )}
        </section>

        <section className="col-span-8 glass-card p-8">
          <div className="flex items-center justify-between mb-7">
            <h3 className="text-lg font-bold headline text-text">Scaling History</h3>
            <span className="text-[10px] font-bold text-textDim uppercase">Recent Actions</span>
          </div>
          <div className="space-y-4 relative">
            <div className="absolute left-6 top-2 bottom-2 w-px bg-[rgba(246,247,235,0.12)]"></div>
            {actions.length === 0 ? (
              <div className="text-textMuted text-xs pl-10">Loading actions...</div>
            ) : (
              actions.slice(0, 8).map((a: any, i: number) => (
                <div key={i} className="relative flex items-center gap-6 pl-4">
                  <div className="relative z-10 w-3 h-3 rounded-full bg-primary ring-4 ring-primary/20 shrink-0"></div>
                  <div className="flex-1 glass-inset p-4 rounded-2xl flex items-center justify-between border-l-2 border-primary hover:border-primary/60 transition-all">
                    <div className="flex items-center gap-5">
                      <div>
                        <div className="text-[10px] text-textDim font-bold mb-0.5">{new Date(a.timestamp).toLocaleTimeString()}</div>
                        <div className="text-sm font-semibold text-text">{a.action?.replace("_", " ")} · {a.target}</div>
                      </div>
                      <div className="text-xs text-textMuted">
                        {a.previous !== undefined ? `${a.previous} → ${a.new}` : ""}
                      </div>
                    </div>
                    <span className="badge">
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
