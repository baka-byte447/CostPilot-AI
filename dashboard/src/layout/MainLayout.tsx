import Sidebar from "./Sidebar";
import Topbar from "./Topbar";
import { runOptimizer } from "@/services/api";

interface MainLayoutProps {
  children: React.ReactNode;
  setPage: (page: string) => void;
  currentPage: string;
  onRefresh?: () => void;
}

export default function MainLayout({ children, setPage, currentPage, onRefresh }: MainLayoutProps) {
  async function handleRunOptimizer() {
    try {
      await runOptimizer();
      if (onRefresh) onRefresh();
    } catch {}
  }

  return (
    <div className="flex min-h-screen bg-surface">
      <Sidebar setPage={setPage} currentPage={currentPage} onRunOptimizer={handleRunOptimizer} />
      <div className="flex-1 ml-64">
        <Topbar onRunOptimizer={handleRunOptimizer} onLoadAll={onRefresh || (() => {})} />
        <main className="mt-14 min-h-screen bg-surface">
          {children}
        </main>
      </div>
    </div>
  );
}