import { useEffect, useState, useRef } from "react";
import { fetchRLExplanation } from "@/services/api";

const ACTION_COLORS: Record<string, string> = {
  scale_up: "bg-primary/20 text-primary border-primary/20",
  maintain: "bg-emerald-400/20 text-emerald-400 border-emerald-400/20",
  scale_down: "bg-amber-400/20 text-amber-400 border-amber-400/20",
};

export default function Explainability() {
  const [current, setCurrent] = useState<any>(null);
  const historyRef = useRef<any[]>([]);
  const [history, setHistory] = useState<any[]>([]);

  useEffect(() => {
    load();
    const interval = setInterval(load, 10000);
    return () => clearInterval(interval);
  }, []);

  async function load() {
    try {
      const res = await fetchRLExplanation();
      const data = res.data;
      if (!data?.explanation) return;
      const e = data.explanation;
      setCurrent(e);

      // Build history (deduplicate by timestamp)
      if (e.timestamp && (historyRef.current.length === 0 || historyRef.current[0].timestamp !== e.timestamp)) {
        historyRef.current = [e, ...historyRef.current].slice(0, 15);
        setHistory([...historyRef.current]);
      }
    } catch {}
  }

  const e = current;

  return (
    <div className="p-10 fade-in">
      <header className="mb-8">
        <h1 className="text-4xl font-extrabold headline text-white tracking-tighter">Explainability</h1>
        <p className="text-slate-400 mt-1.5 text-sm">Human-readable AI decision audit trail</p>
      </header>

      {/* Current Explanation */}
      <div className="glass-panel p-7 rounded-xl mb-6">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-primary">visibility</span>
            <h3 className="text-base font-bold headline text-white">Current Explanation</h3>
          </div>
          <span className="px-2 py-0.5 bg-secondary/20 text-secondary text-[9px] font-bold uppercase rounded-full border border-secondary/20">
            {e?.source ?? "—"}
          </span>
        </div>

        <div className="bg-[#272a31]/40 p-6 rounded-xl mb-5">
          <p className="text-sm text-on-surface leading-relaxed">
            {e?.explanation ?? "Loading explanation..."}
          </p>
        </div>

        <div className="grid grid-cols-4 gap-4">
          <div className="bg-[#272a31] p-4 rounded-xl">
            <div className="flex items-center gap-1.5 text-[9px] text-slate-500 uppercase mb-2">
              <span className="material-symbols-outlined text-xs">bolt</span>Action
            </div>
            <div className="text-sm font-bold text-primary">{e?.action?.replace("_", " ").toUpperCase() ?? "—"}</div>
          </div>
          <div className="bg-[#272a31] p-4 rounded-xl">
            <div className="flex items-center gap-1.5 text-[9px] text-slate-500 uppercase mb-2">
              <span className="material-symbols-outlined text-xs">memory</span>CPU
            </div>
            <div className="text-sm font-bold text-primary">{e ? e.cpu + "%" : "—"}</div>
          </div>
          <div className="bg-[#272a31] p-4 rounded-xl">
            <div className="flex items-center gap-1.5 text-[9px] text-slate-500 uppercase mb-2">
              <span className="material-symbols-outlined text-xs">storage</span>Memory
            </div>
            <div className="text-sm font-bold text-secondary">{e ? e.memory + "%" : "—"}</div>
          </div>
          <div className="bg-[#272a31] p-4 rounded-xl">
            <div className="flex items-center gap-1.5 text-[9px] text-slate-500 uppercase mb-2">
              <span className="material-symbols-outlined text-xs">dynamic_feed</span>Replicas
            </div>
            <div className="text-sm font-bold text-amber-400">{e?.replicas ?? "—"}</div>
          </div>
        </div>
      </div>

      {/* History */}
      <div className="glass-panel p-7 rounded-xl">
        <h3 className="text-base font-bold headline text-white mb-5">Explanation History</h3>
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {history.length === 0 ? (
            <div className="text-slate-600 text-xs text-center py-8">
              No history yet — decisions will appear here every 10 seconds
            </div>
          ) : (
            history.map((h, i) => (
              <div key={i} className="bg-[#272a31]/40 rounded-xl p-5 border border-[#3c4a46]/10">
                <div className="flex items-center gap-2 mb-3">
                  <span className={`px-2 py-0.5 text-[9px] font-bold uppercase rounded-full border ${ACTION_COLORS[h.action] ?? "bg-slate-700 text-slate-400 border-slate-600"}`}>
                    {h.action?.replace("_", " ") ?? "—"}
                  </span>
                  <span className="px-2 py-0.5 bg-secondary/20 text-secondary text-[9px] font-bold uppercase rounded-full border border-secondary/20">
                    {h.source}
                  </span>
                  <span className="text-[10px] font-mono text-slate-600 ml-auto">
                    {h.timestamp ? new Date(h.timestamp).toLocaleTimeString() : "—"}
                  </span>
                </div>
                <p className="text-xs text-slate-400 leading-relaxed">{h.explanation}</p>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}