from __future__ import annotations

from dev_right_hand.agents.base import BaseAgent
from dev_right_hand.contracts import AgentMetric, Finding, FindingCategory, RepositoryContext, Severity


class MLValidationAgent(BaseAgent):
    name = "MLValidationAgent"

    def analyze(
        self, context: RepositoryContext
    ) -> tuple[list[Finding], list[AgentMetric], str]:
        findings: list[Finding] = []
        training_related = [
            path
            for path in context.python_files
            if any(token in path.name.lower() for token in ("train", "fit", "model", "feature"))
        ]

        if training_related and not context.test_files:
            findings.append(
                Finding(
                    agent_name=self.name,
                    category=FindingCategory.ML_VALIDATION,
                    severity=Severity.HIGH,
                    title="Training code without protection tests",
                    description="Training-related modules were detected but no tests are present.",
                    recommendation="Add regression tests for training pipelines and threshold-based metric assertions.",
                )
            )

        if training_related and not any("mlflow" in path.name.lower() for path in context.config_files):
            findings.append(
                Finding(
                    agent_name=self.name,
                    category=FindingCategory.ML_VALIDATION,
                    severity=Severity.MEDIUM,
                    title="Experiment tracking integration not detected",
                    description="Training-related code exists, but experiment tracking signals were not found.",
                    recommendation="Integrate experiment tracking to persist params, metrics, models and lineage.",
                )
            )

        if not training_related:
            findings.append(
                Finding(
                    agent_name=self.name,
                    category=FindingCategory.ML_VALIDATION,
                    severity=Severity.INFO,
                    title="No explicit training modules found",
                    description="The current repository does not yet expose obvious model training modules.",
                    recommendation="Keep this agent enabled for future ML workflows as the project evolves.",
                )
            )

        metrics = [
            AgentMetric(name="training_related_files", value=len(training_related)),
            AgentMetric(name="model_files", value=len(context.model_files)),
        ]
        summary = "Assessed training workflow signals, reproducibility hooks and metric governance readiness."
        return findings, metrics, summary
