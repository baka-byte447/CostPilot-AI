import axios from "axios"

const api = axios.create({
  baseURL: "",
  timeout: 10000,
})

export const fetchMetrics       = () => api.get("/api/metrics")
export const fetchForecast      = () => api.get("/api/forecast/system")
export const fetchCostForecast  = () => api.get("/api/cost/forecast")
export const runOptimizer       = () => api.post("/api/optimize/scale")

export const fetchRLStats       = () => api.get("/api/rl/stats")
export const fetchRLDecision    = () => api.get("/api/rl/decision/latest")
export const fetchRLExplanation = () => api.get("/api/rl/explanation/latest")
export const fetchAWSState      = () => api.get("/api/rl/aws/state")

export const fetchSLOConfig     = () => api.get("/api/optimize/slo")
export const fetchSafetyStatus  = () => api.get("/api/optimize/safety/status")
export const fetchOptimizerPreview = () => api.get("/api/optimize/preview")

export const fetchAzureACI      = () => api.get("/api/azure/aci")
export const fetchAzureCost     = () => api.get("/api/azure/cost/current-month")
export const fetchAWSCost       = () => api.get("/api/aws/cost/current-month")
export const fetchAzureCostByService = () => api.get("/api/azure/cost/by-service")

export const fetchAWSASGs       = () => api.get("/api/aws/ec2/asgs")
export const fetchAWSClusters   = () => api.get("/api/aws/ecs/clusters")
export const fetchAWSActions    = () => api.get("/api/aws/actions/log")

// ── Auth ──
export const authRegister       = (email: string, password: string) => api.post("/api/auth/register", { email, password })
export const authLogin          = (email: string, password: string) => api.post("/api/auth/login", { email, password })

// ── AWS Connection Flow ──
export const awsSetup           = (control_account_id: string, role_name?: string, allow_write?: boolean) =>
  api.post("/api/aws/connection/setup", { control_account_id, role_name: role_name || "CostPilotAccessRole", allow_write: allow_write || false })
export const awsSaveConnection  = (data: { account_id: string; role_arn: string; external_id: string; regions: string[]; label?: string }) =>
  api.post("/api/aws/connection", data)
export const awsGetConnection   = () => api.get("/api/aws/connection")
export const awsDeleteConnection = () => api.delete("/api/aws/connection")
export const awsVerifyConnection = () => api.get("/api/aws/connection/verify")

export default api