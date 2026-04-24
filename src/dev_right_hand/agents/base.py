from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from dev_right_hand.contracts import AgentMetric, AgentReport, Finding, RepositoryContext


class BaseAgent(ABC):
    name: str

    def run(self, context: RepositoryContext) -> AgentReport:
        started_at = datetime.utcnow()
        try:
            findings, metrics, summary = self.analyze(context)
            return AgentReport(
                agent_name=self.name,
                summary=summary,
                findings=findings,
                metrics=metrics,
                started_at=started_at,
                finished_at=datetime.utcnow(),
            )
        except Exception as exc:  # pragma: no cover - defensive path
            return AgentReport(
                agent_name=self.name,
                summary="Agent execution failed.",
                started_at=started_at,
                finished_at=datetime.utcnow(),
                succeeded=False,
                error_message=str(exc),
            )

    @abstractmethod
    def analyze(
        self, context: RepositoryContext
    ) -> tuple[list[Finding], list[AgentMetric], str]:
        raise NotImplementedError
