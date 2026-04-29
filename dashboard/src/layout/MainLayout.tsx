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
    <div className="flex min-h-screen bg-[#0f1012]">
      <Sidebar setPage={setPage} currentPage={currentPage} onRunOptimizer={handleRunOptimizer} />
      <div className="flex-1 ml-64">
        <Topbar onRunOptimizer={handleRunOptimizer} onLoadAll={onRefresh || (() => {})} />
        <main className="mt-14 min-h-screen bg-[#0f1012]">
          {children}
        </main>
      </div>
    </div>
  );
}