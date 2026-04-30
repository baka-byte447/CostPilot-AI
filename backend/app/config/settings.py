"""Centralized configuration for the backend service."""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field

try:
	from pydantic_settings import BaseSettings, SettingsConfigDict
	USING_PYDANTIC_V2 = True
except ImportError:  # pragma: no cover - compatibility fallback
	from pydantic import BaseSettings
	USING_PYDANTIC_V2 = False


class Settings(BaseSettings):
	app_name: str = Field("costpilot-backend", description="Display name for the backend service")
	database_url: str = Field("sqlite:///../database/metrics.db", description="SQLAlchemy database URL")
	prometheus_url: str = Field("http://prometheus:9090", description="Base URL for Prometheus queries")
	cors_origins: str = Field("*", description="Comma-separated list of allowed CORS origins")
	prometheus_export_port: int = Field(8001, description="Port for the internal Prometheus exporter")
	kube_config_path: Optional[str] = Field(None, description="Optional path to a kubeconfig file")
	aws_control_account_id: Optional[str] = Field(
		None,
		description="AWS account ID that hosts the CostPilot control plane",
	)
	aws_default_region: str = Field("us-east-1", description="Default region for AWS client sessions")
	aws_require_connection: bool = Field(
		False,
		description="Require a stored AWS connection for AWS API calls",
	)
	aws_assume_role_duration_seconds: int = Field(
		3600,
		description="STS assume role session duration in seconds",
	)
	auth_required: bool = Field(
		False,
		description="Require JWT authentication for protected endpoints",
	)
	jwt_secret: str = Field(
		"change-me",
		description="Secret key for signing JWTs",
	)
	jwt_algorithm: str = Field(
		"HS256",
		description="JWT signing algorithm",
	)
	jwt_access_token_minutes: int = Field(
		720,
		description="JWT access token lifetime in minutes",
	)

	if USING_PYDANTIC_V2:
		model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
	else:
		class Config:
			env_file = ".env"
			env_file_encoding = "utf-8"

	@property
	def resolved_database_url(self) -> str:
		"""Resolve relative SQLite paths to absolute locations."""
		if not self.database_url.startswith("sqlite:///"):
			return self.database_url

		raw_path = self.database_url.replace("sqlite:///", "", 1)
		db_path = Path(__file__).resolve().parents[2] / raw_path
		db_path.parent.mkdir(parents=True, exist_ok=True)
		return f"sqlite:///{db_path}"


@lru_cache
def get_settings() -> Settings:
	return Settings()


settings = get_settings()
