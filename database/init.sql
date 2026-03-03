-- CostPilot-AI Database Schema

-- Metrics table: stores raw telemetry data
CREATE TABLE IF NOT EXISTS metrics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    resource_type VARCHAR(50),  -- CPU, Memory, I/O, etc.
    resource_id VARCHAR(100),   -- instance_id, pod_name, etc.
    value FLOAT,
    unit VARCHAR(20)
);

-- Cost table: billing and cost data
CREATE TABLE IF NOT EXISTS costs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    resource_id VARCHAR(100),
    cost FLOAT,
    currency VARCHAR(10),
    provider VARCHAR(50)  -- AWS, Azure, GCP
);

-- Forecasts table: predicted demand
CREATE TABLE IF NOT EXISTS forecasts (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP NOT NULL,
    forecast_time TIMESTAMP NOT NULL,
    metric_type VARCHAR(50),
    predicted_value FLOAT,
    confidence FLOAT
);

-- Audit log: tracks all decisions
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    action VARCHAR(255),
    state_before JSON,
    state_after JSON,
    decision_rationale TEXT,
    status VARCHAR(20)  -- success, failed, rollback
);

-- SLA Compliance table
CREATE TABLE IF NOT EXISTS sla_compliance (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    metric_name VARCHAR(100),
    target_value FLOAT,
    actual_value FLOAT,
    compliant BOOLEAN
);

-- Create indices for performance
CREATE INDEX idx_metrics_timestamp ON metrics(timestamp);
CREATE INDEX idx_costs_timestamp ON costs(timestamp);
CREATE INDEX idx_forecasts_time ON forecasts(forecast_time);
CREATE INDEX idx_audit_timestamp ON audit_log(timestamp);
