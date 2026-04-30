# config.py — Central configuration loaded from .env file
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# --- AWS ---
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "ap-south-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
AWS_REGIONS = [r.strip() for r in os.getenv("AWS_REGIONS", "").split(",") if r.strip()]

# --- AI Models ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")


# --- Thresholds ---
SNAPSHOT_AGE_DAYS = int(os.getenv("SNAPSHOT_AGE_DAYS", "30"))
EC2_CPU_THRESHOLD = float(os.getenv("EC2_CPU_THRESHOLD", "5.0"))

# --- Optimizer ---
OPTIMIZER_LOOKBACK_DAYS = int(os.getenv("OPTIMIZER_LOOKBACK_DAYS", "7"))
OPTIMIZER_METRIC_PERIOD = int(os.getenv("OPTIMIZER_METRIC_PERIOD", "3600"))
OPTIMIZER_FORECAST_HORIZON_HOURS = int(os.getenv("OPTIMIZER_FORECAST_HORIZON_HOURS", "24"))
OPTIMIZER_MAX_RESOURCES = int(os.getenv("OPTIMIZER_MAX_RESOURCES", "200"))
OPTIMIZER_CPU_LOW_PCT = float(os.getenv("OPTIMIZER_CPU_LOW_PCT", "15.0"))
OPTIMIZER_CPU_HIGH_PCT = float(os.getenv("OPTIMIZER_CPU_HIGH_PCT", "80.0"))
OPTIMIZER_ALLOW_EC2_STOP = os.getenv("OPTIMIZER_ALLOW_EC2_STOP", "false").lower() == "true"
OPTIMIZER_ALLOW_EC2_RESIZE = os.getenv("OPTIMIZER_ALLOW_EC2_RESIZE", "true").lower() == "true"
OPTIMIZER_ALLOW_RDS_STOP = os.getenv("OPTIMIZER_ALLOW_RDS_STOP", "false").lower() == "true"
OPTIMIZER_MIN_CONFIDENCE = float(os.getenv("OPTIMIZER_MIN_CONFIDENCE", "0.6"))
OPTIMIZER_MAX_EXPLANATIONS = int(os.getenv("OPTIMIZER_MAX_EXPLANATIONS", "10"))
AUTO_APPLY_OPTIMIZATIONS = os.getenv("AUTO_APPLY_OPTIMIZATIONS", "false").lower() == "true"

# --- Forecasting / RL / SLO ---
FORECAST_MODEL_MIN_POINTS = int(os.getenv("FORECAST_MODEL_MIN_POINTS", "21"))
LSTM_EPOCHS = int(os.getenv("LSTM_EPOCHS", "120"))
LSTM_HIDDEN_SIZE = int(os.getenv("LSTM_HIDDEN_SIZE", "12"))
LSTM_LEARNING_RATE = float(os.getenv("LSTM_LEARNING_RATE", "0.01"))
LSTM_SEQUENCE_LENGTH = int(os.getenv("LSTM_SEQUENCE_LENGTH", "6"))
RL_QTABLE_PATH = os.getenv("RL_QTABLE_PATH", "rl_models/q_table.npy")
RL_ALPHA = float(os.getenv("RL_ALPHA", "0.1"))
RL_GAMMA = float(os.getenv("RL_GAMMA", "0.9"))
RL_EPSILON = float(os.getenv("RL_EPSILON", "0.1"))
SLO_MAX_CPU = float(os.getenv("SLO_MAX_CPU", "85"))
SLO_MAX_MEMORY = float(os.getenv("SLO_MAX_MEMORY", "90"))
SLO_MAX_REQUESTS = float(os.getenv("SLO_MAX_REQUESTS", "2.0"))
SLO_MIN_REPLICAS = int(os.getenv("SLO_MIN_REPLICAS", "1"))
SLO_MAX_REPLICAS = int(os.getenv("SLO_MAX_REPLICAS", "8"))
SLO_MAX_SCALE_STEP = int(os.getenv("SLO_MAX_SCALE_STEP", "2"))
SLO_COOLDOWN_SECONDS = int(os.getenv("SLO_COOLDOWN_SECONDS", "180"))

# --- Database ---
DB_PATH = os.getenv("DB_PATH", "db/optimizer.db")

# --- Budget Alert ---
BUDGET_THRESHOLD = float(os.getenv("BUDGET_THRESHOLD", "50.00"))

# --- Email / SMTP ---
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
ALERT_FROM = os.getenv("ALERT_FROM", "")
ALERT_TO = os.getenv("ALERT_TO", "")

# --- Cost estimates (USD per month) ---
EBS_COST_PER_GB = 0.10
EIP_MONTHLY_COST = 3.60
SNAPSHOT_COST_PER_GB = 0.05
STOPPED_EC2_EBS_ESTIMATE = 5.00
