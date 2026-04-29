import { useState, useEffect } from "react";
import { fetchSafetyStatus } from "@/services/api";

interface TopbarProps {
  onRunOptimizer: () => void;
  onLoadAll: () => void;
}

export default function Topbar({ onRunOptimizer, onLoadAll }: TopbarProps) {
  const [cooldown, setCooldown] = useState<{ active: boolean; remaining: number }>({
    active: false,
    remaining: 0,
  });

  useEffect(() => {
    checkCooldown();
    const interval = setInterval(checkCooldown, 5000);
    return () => clearInterval(interval);
  }, []);

  async function checkCooldown() {
    try {
      const res = await fetchSafetyStatus();
      const s = res.data;
      if (s?.cooldown_active) {
        setCooldown({ active: true, remaining: s.cooldown_remaining });
      } else {
        setCooldown({ active: false, remaining: 0 });
      }
    } catch {}
  }

  const handleRefresh = () => {
    onLoadAll();
  };

  const handleRunOptimizer = () => {
    onRunOptimizer();
  };

  return (
    <header className="fixed top-0 right-0 left-64 h-14 topbar-shell rounded-b-2xl flex items-center justify-between px-8 z-40">
      <div className="flex items-center gap-6">
        <div className="relative">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 material-symbols-outlined text-textDim text-sm">search</span>
          <input
            className="glass-input rounded-full py-1.5 pl-9 pr-4 text-xs w-56 focus:outline-none focus:ring-1 ring-primary/40 text-text placeholder:text-textDim"
            placeholder="Global search..."
            type="text"
          />
        </div>
        <nav className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-textDim">
          <span className="px-2.5 py-1 rounded-full border-[1.5px] border-primary bg-transparent text-primary">
            LIVE BACKEND
          </span>
          <span>Production / Staging / Dev views are not separate targets yet.</span>
        </nav>
      </div>

      <div className="flex items-center gap-3">
        {cooldown.active && (
          <div className="flex items-center gap-1.5 px-3 py-1 glass-pill text-primary text-[10px] font-bold uppercase">
            <span className="w-1.5 h-1.5 rounded-full bg-primary breathing-pulse"></span>
            Cooldown <span>{cooldown.remaining}s</span>
          </div>
        )}

        <div className="flex items-center gap-1.5 px-3 py-1 glass-pill text-primary text-[10px] font-bold uppercase tracking-widest">
          <span className="w-1.5 h-1.5 rounded-full live-dot breathing-pulse"></span>
          LIVE
        </div>

        <button
          onClick={handleRefresh}
          className="px-3 py-1.5 rounded-full ghost-button text-xs font-semibold"
        >
          Refresh
        </button>

        <button
          onClick={handleRunOptimizer}
          className="px-3 py-1.5 rounded-[8px] optimizer-gradient text-xs font-semibold"
        >
          Run Optimizer
        </button>

        <div className="h-5 w-px bg-[rgba(246,247,235,0.12)] mx-1"></div>

        <span className="material-symbols-outlined text-textDim hover:text-primary cursor-pointer transition-colors text-xl">notifications</span>
        <span className="material-symbols-outlined text-textDim hover:text-primary cursor-pointer transition-colors text-xl">settings</span>

        <div className="w-7 h-7 rounded-full bg-primary/15 border border-primary/40 flex items-center justify-center text-primary text-xs font-bold">
          AD
        </div>
      </div>
    </header>
  );
}