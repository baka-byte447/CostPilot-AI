interface SidebarProps {
  setPage: (page: string) => void;
  currentPage: string;
  onRunOptimizer: () => void;
}

const navItems = [
  { id: "overview", icon: "dashboard", label: "Overview", group: "Platform" },
  { id: "liveinfra", icon: "hub", label: "Live Infra", group: "Platform" },
  { id: "intelligence", icon: "insights", label: "Intelligence", group: "Platform" },
  { id: "aioptimizer", icon: "psychology", label: "AI Optimizer", group: "AI Engine" },
  { id: "governance", icon: "gavel", label: "Governance", group: "AI Engine" },
  { id: "explainability", icon: "visibility", label: "Explainability", group: "AI Engine" },
  { id: "connectaws", icon: "cloud_sync", label: "Connect AWS", group: "Cloud" },
  { id: "resources", icon: "cloud", label: "Resources", group: "Infrastructure" },
];

export default function Sidebar({ setPage, currentPage, onRunOptimizer }: SidebarProps) {
  const groups = ["Platform", "AI Engine", "Cloud", "Infrastructure"];

  const handleRunOptimizer = () => {
    onRunOptimizer();
  };

  return (
    <aside className="flex flex-col fixed left-0 top-0 h-full w-64 sidebar-shell border-r border-[rgba(255,255,255,0.08)] z-50 overflow-y-auto">
      <div className="p-7 flex items-center gap-3 border-b border-[rgba(255,255,255,0.08)]">
        <div className="w-9 h-9 rounded-xl bg-primary/15 border border-primary/40 flex items-center justify-center shadow-[0_0_18px_rgba(233,79,55,0.35)]">
          <span className="material-symbols-outlined text-primary text-xl" style={{ fontVariationSettings: "'FILL' 0" }}>hub</span>
        </div>
        <div>
          <div className="text-[18px] font-bold text-text tracking-tighter font-headline">CostPilot</div>
          <div className="text-[9px] uppercase tracking-[0.2em] text-textDim font-bold">Enterprise AI</div>
        </div>
      </div>

      <nav className="flex-1 px-3 py-5 space-y-1">
        {groups.map((group) => (
          <div key={group}>
            <p className="px-4 text-[9px] font-bold text-textDim uppercase tracking-widest mb-2 mt-5 first:mt-0">{group}</p>
            {navItems
              .filter((item) => item.group === group)
              .map((item) => (
                <button
                  key={item.id}
                  onClick={() => setPage(item.id)}
                  className={`nav-item w-full text-left flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-semibold font-headline transition-all ${
                    currentPage === item.id ? "nav-active" : "nav-inactive"
                  }`}
                >
                  <span className="material-symbols-outlined text-[18px]">{item.icon}</span>
                  {item.label}
                </button>
              ))}
          </div>
        ))}
      </nav>

      <div className="p-5 border-t border-[rgba(255,255,255,0.08)]">
        <button
          onClick={handleRunOptimizer}
          className="w-full py-3 rounded-[10px] optimizer-gradient optimizer-glow text-sm font-medium flex items-center justify-center gap-2"
        >
          <span className="text-base leading-none">+</span>
          Run Optimizer
        </button>
      </div>
    </aside>
  );
}