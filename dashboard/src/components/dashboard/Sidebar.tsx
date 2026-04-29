import { LayoutDashboard, Activity, Brain, ShieldCheck, MessageSquare, CloudCog, DollarSign, Zap } from "lucide-react"
import type { FC } from "react"

interface SidebarProps {
  currentTab: string
  setTab: (val: string) => void
}

const NAV = [
  {
    group: "PLATFORM",
    items: [
      { id: "overview",     label: "Overview",        icon: LayoutDashboard },
      { id: "metrics",      label: "Live Metrics",    icon: Activity },
      { id: "cost",         label: "Cost Intelligence", icon: DollarSign },
    ]
  },
  {
    group: "AI ENGINE",
    items: [
      { id: "rl",           label: "RL Agent",        icon: Brain },
      { id: "safety",       label: "Safety Engine",   icon: ShieldCheck },
      { id: "explain",      label: "Explainability",  icon: MessageSquare },
    ]
  },
  {
    group: "INFRASTRUCTURE",
    items: [
      { id: "aws",          label: "AWS Resources",   icon: CloudCog },
      { id: "azure",        label: "Azure Resources", icon: CloudCog },
    ]
  },
]

const Sidebar: FC<SidebarProps> = ({ currentTab, setTab }) => {
  return (
    <aside className="w-56 bg-surface border-r border-surfaceBorder flex flex-col shrink-0 fixed left-0 top-0 bottom-0 z-20">
      <div className="px-4 py-5 border-b border-surfaceBorder">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-md bg-cyan/10 border border-cyan/30 flex items-center justify-center">
            <Zap size={14} className="text-cyan" />
          </div>
          <div>
            <p className="text-[13px] font-semibold text-text leading-tight">NimbusOpt</p>
            <p className="text-[10px] text-textMuted font-mono">v0.1.0 · live</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-5 overflow-y-auto">
        {NAV.map(group => (
          <div key={group.group}>
            <p className="text-[10px] font-mono font-semibold text-textDim tracking-widest px-3 mb-1.5 select-none">
              {group.group}
            </p>
            <div className="space-y-0.5">
              {group.items.map(item => {
                const active = currentTab === item.id
                return (
                  <button
                    key={item.id}
                    onClick={() => setTab(item.id)}
                    className={`nav-item ${active ? "nav-item-active" : "nav-item-inactive"}`}
                  >
                    <item.icon size={15} />
                    <span>{item.label}</span>
                  </button>
                )
              })}
            </div>
          </div>
        ))}
      </nav>

      <div className="px-4 py-4 border-t border-surfaceBorder">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-full bg-surfaceHigh border border-surfaceBorder flex items-center justify-center text-textMuted text-[11px] font-mono font-semibold select-none">
            AD
          </div>
          <div className="min-w-0">
            <p className="text-[12px] font-medium text-text truncate">Admin</p>
            <p className="text-[10px] text-textMuted font-mono truncate">nimbusopt-agent</p>
          </div>
        </div>
      </div>
    </aside>
  )
}

export default Sidebar