from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class StringEnum(str, Enum):
    """Backport-friendly string enum for Python 3.10+ environments."""


class Severity(StringEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FindingCategory(StringEnum):
    CODE_QUALITY = "code_quality"
    DATA_QUALITY = "data_quality"
    ML_VALIDATION = "ml_validation"
    LLM_SAFETY = "llm_safety"
    OBSERVABILITY = "observability"


class Finding(BaseModel):
    agent_name: str
    category: FindingCategory
    severity: Severity
    title: str
    description: str
    file_path: Path | None = None
    recommendation: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentMetric(BaseModel):
    name: str
    value: float | int | str
    unit: str | None = None


class RepositoryContext(BaseModel):
    repository_root: Path
    python_files: list[Path]
    test_files: list[Path]
    config_files: list[Path]
    model_files: list[Path]
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AgentReport(BaseModel):
    agent_name: str
    summary: str
    findings: list[Finding] = Field(default_factory=list)
    metrics: list[AgentMetric] = Field(default_factory=list)
    started_at: datetime
    finished_at: datetime
    succeeded: bool = True
    error_message: str | None = None


class ExecutionEvent(BaseModel):
    run_id: str
    agent_name: str
    status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: dict[str, Any] = Field(default_factory=dict)


class RepositoryAnalysisReport(BaseModel):
    run_id: str
    repository_root: Path
    created_at: datetime = Field(default_factory=datetime.utcnow)
    agent_reports: list[AgentReport]

    @property
    def findings(self) -> list[Finding]:
        return [finding for report in self.agent_reports for finding in report.findings]
