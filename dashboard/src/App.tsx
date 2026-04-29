import { useState } from "react";
import MainLayout from "./layout/MainLayout";
import { runOptimizer } from "./services/api";
import CustomCursor from "./components/CustomCursor";

import Overview from "./pages/Overview";
import LiveInfra from "./pages/LiveInfra";
import Intelligence from "./pages/Intelligence";
import AIOptimizer from "./pages/AIOptimizer";
import Governance from "./pages/Governance";
import Explainability from "./pages/Explainability";
import Resources from "./pages/Resources";

function App() {
  const [page, setPage] = useState("overview");
  const [refreshKey, setRefreshKey] = useState(0);

  function handleRefresh() {
    setRefreshKey(k => k + 1);
  }

  const renderPage = () => {
    switch (page) {
      case "overview": return <Overview key={refreshKey} onNavigate={setPage} onRunOptimizer={handleRunOptimizer} />;
      case "liveinfra": return <LiveInfra key={refreshKey} />;
      case "intelligence": return <Intelligence key={refreshKey} />;
      case "aioptimizer": return <AIOptimizer key={refreshKey} onRunOptimizer={handleRunOptimizer} />;
      case "governance": return <Governance key={refreshKey} />;
      case "explainability": return <Explainability key={refreshKey} />;
      case "resources": return <Resources key={refreshKey} />;
      default: return <Overview key={refreshKey} onNavigate={setPage} onRunOptimizer={handleRunOptimizer} />;
    }
  };

  async function handleRunOptimizer() {
    try {
      await runOptimizer();
      handleRefresh();
    } catch {}
  }

  return (
    <MainLayout setPage={setPage} currentPage={page} onRefresh={handleRefresh}>
      {renderPage()}
      <CustomCursor />
    </MainLayout>
  );
}

export default App;