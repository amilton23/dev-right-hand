from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class TrackingSettings(BaseModel):
    enabled: bool = True
    sink: str = "stdout"


class ThresholdSettings(BaseModel):
    min_test_files: int = 1
    min_training_files: int = 1
    max_critical_findings: int = 0


class AppConfig(BaseModel):
    repository_root: Path
    tracking: TrackingSettings = Field(default_factory=TrackingSettings)
    thresholds: ThresholdSettings = Field(default_factory=ThresholdSettings)
