import { useEffect, useState } from "react";
import { getMetrics, getForecast, getCostForecast } from "./services/api";

import MetricsChart from "./components/MetricsChart";
import ForecastChart from "./components/ForecastChart";
import CostPanel from "./components/CostPanel";
import ScalingPanel from "./components/ScalingPanel";

function App() {

  const [metrics, setMetrics] = useState([]);
  const [forecast, setForecast] = useState([]);
  const [cost, setCost] = useState<any>(null);

  useEffect(() => {

    getMetrics().then(res => setMetrics(res.data));

    getForecast().then(res => {
      setForecast(res.data.cpu_forecast);
    });

    getCostForecast().then(res => setCost(res.data));

  }, []);

  return (
    <div>

      <h1>Autonomous Cloud Cost Intelligence</h1>

      <MetricsChart data={metrics} />

      <ForecastChart data={forecast} />

      {cost && <CostPanel cost={cost} />}

      <ScalingPanel />

    </div>
  );
}

export default App;

