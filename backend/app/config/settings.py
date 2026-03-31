"""Centralized configuration for the backend service."""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
	app_name: str = Field("costpilot-backend", description="Display name for the backend service")
	database_url: str = Field("sqlite:///../database/metrics.db", description="SQLAlchemy database URL")
	prometheus_url: str = Field("http://prometheus:9090", description="Base URL for Prometheus queries")
	prometheus_export_port: int = Field(8001, description="Port for the internal Prometheus exporter")
	kube_config_path: Optional[str] = Field(None, description="Optional path to a kubeconfig file")

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
