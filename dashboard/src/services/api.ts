import axios from "axios"

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
  timeout: 10000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("costpilot_token");
  if (token) {
    config.headers.set("Authorization", `Bearer ${token}`);
  }
  return config;
});

export const fetchMetrics       = () => api.get("/metrics")
export const fetchForecast      = () => api.get("/forecast/system")
export const fetchCostForecast  = () => api.get("/forecast/cost")
export const runOptimizer       = () => api.post("/optimize/scale")

export const fetchRLStats       = () => api.get("/rl/stats")
export const fetchRLDecision    = () => api.get("/rl/decision/latest")
export const fetchRLExplanation = () => api.get("/rl/explanation/latest")
export const fetchAWSState      = () => api.get("/rl/aws/state")

export const fetchSLOConfig     = () => api.get("/optimize/slo")
export const fetchSafetyStatus  = () => api.get("/optimize/safety/status")

export const fetchAzureACI      = () => api.get("/azure/aci")
export const fetchAzureCost     = () => api.get("/azure/cost/current-month")
export const fetchAzureCostByService = () => api.get("/azure/cost/by-service")

export const fetchAWSASGs       = () => api.get("/aws/ec2/asgs")
export const fetchAWSClusters   = () => api.get("/aws/ecs/clusters")
export const fetchAWSActions    = () => api.get("/aws/actions/log")

export default api