from __future__ import annotations

from dev_right_hand.agents.base import BaseAgent
from dev_right_hand.contracts import AgentMetric, Finding, FindingCategory, RepositoryContext, Severity


class DataQualityAgent(BaseAgent):
    name = "DataQualityAgent"

    def analyze(
        self, context: RepositoryContext
    ) -> tuple[list[Finding], list[AgentMetric], str]:
        findings: list[Finding] = []
        data_contract_files = [
            path for path in context.config_files if path.name.startswith(("schema", "contract"))
        ]

        if not data_contract_files:
            findings.append(
                Finding(
                    agent_name=self.name,
                    category=FindingCategory.DATA_QUALITY,
                    severity=Severity.MEDIUM,
                    title="No data contracts detected",
                    description="No schema or contract files were detected for data validation workflows.",
                    recommendation="Add explicit schema definitions or validation specs for input and output datasets.",
                )
            )

        if not any("data" in part.lower() for path in context.python_files for part in path.parts):
            findings.append(
                Finding(
                    agent_name=self.name,
                    category=FindingCategory.DATA_QUALITY,
                    severity=Severity.LOW,
                    title="Data validation layer not obvious",
                    description="The repository structure does not clearly expose a data quality or validation module.",
                    recommendation="Consider a dedicated package for schema checks, freshness and input validation.",
                )
            )

        metrics = [
            AgentMetric(name="data_contract_files", value=len(data_contract_files)),
        ]
        summary = "Checked repository signals for data contracts, validation and data quality readiness."
        return findings, metrics, summary
