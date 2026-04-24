from __future__ import annotations

from dev_right_hand.agents.base import BaseAgent
from dev_right_hand.contracts import AgentMetric, Finding, FindingCategory, RepositoryContext, Severity


class ObservabilityAgent(BaseAgent):
    name = "ObservabilityAgent"

    def analyze(
        self, context: RepositoryContext
    ) -> tuple[list[Finding], list[AgentMetric], str]:
        findings: list[Finding] = []
        log_related = [
            path for path in context.python_files if any(token in path.name.lower() for token in ("log", "trace"))
        ]

        if not log_related:
            findings.append(
                Finding(
                    agent_name=self.name,
                    category=FindingCategory.OBSERVABILITY,
                    severity=Severity.MEDIUM,
                    title="Observability modules not detected",
                    description="The repository does not clearly expose logging, metrics or tracing components yet.",
                    recommendation="Create a shared observability layer with structured logs, metrics and traces.",
                )
            )

        findings.append(
            Finding(
                agent_name=self.name,
                category=FindingCategory.OBSERVABILITY,
                severity=Severity.LOW,
                title="Alert strategy should be defined",
                description="Operational ownership is stronger when the project defines alerts and recovery playbooks.",
                recommendation="Define SLAs, threshold alerts and incident response paths for critical workflows.",
            )
        )

        metrics = [
            AgentMetric(name="observability_related_files", value=len(log_related)),
        ]
        summary = "Assessed logging, tracing, metrics and operational readiness signals."
        return findings, metrics, summary
