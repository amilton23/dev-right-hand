from __future__ import annotations

from pathlib import Path

from dev_right_hand.agents.base import BaseAgent
from dev_right_hand.contracts import AgentMetric, Finding, FindingCategory, RepositoryContext, Severity


class CodeReviewAgent(BaseAgent):
    name = "CodeReviewAgent"

    def analyze(
        self, context: RepositoryContext
    ) -> tuple[list[Finding], list[AgentMetric], str]:
        findings: list[Finding] = []
        python_file_count = len(context.python_files)

        if python_file_count == 0:
            findings.append(
                Finding(
                    agent_name=self.name,
                    category=FindingCategory.CODE_QUALITY,
                    severity=Severity.MEDIUM,
                    title="No Python source files found",
                    description="The repository does not contain Python modules to analyze.",
                    recommendation="Add Python package structure or point the scanner to the correct directory.",
                )
            )

        if context.python_files and not context.test_files:
            findings.append(
                Finding(
                    agent_name=self.name,
                    category=FindingCategory.CODE_QUALITY,
                    severity=Severity.HIGH,
                    title="Tests are missing",
                    description="Python source files were found but there are no test files in the repository.",
                    recommendation="Create unit and integration test suites to protect the main workflows.",
                )
            )

        if not any(path.name == "pyproject.toml" for path in context.config_files):
            findings.append(
                Finding(
                    agent_name=self.name,
                    category=FindingCategory.CODE_QUALITY,
                    severity=Severity.MEDIUM,
                    title="Project configuration is incomplete",
                    description="A `pyproject.toml` file was not found, which makes tooling harder to standardize.",
                    recommendation="Adopt `pyproject.toml` for formatting, linting, packaging and test configuration.",
                )
            )

        long_named_files = [path for path in context.python_files if len(path.stem) > 32]
        for path in long_named_files[:3]:
            findings.append(
                Finding(
                    agent_name=self.name,
                    category=FindingCategory.CODE_QUALITY,
                    severity=Severity.LOW,
                    title="Potentially overloaded module name",
                    description=(
                        f"The module `{path.name}` has a long name, which can be a smell of unclear boundaries."
                    ),
                    file_path=path,
                    recommendation="Review if the module responsibility can be simplified or better scoped.",
                )
            )

        metrics = [
            AgentMetric(name="python_files", value=python_file_count),
            AgentMetric(name="test_files", value=len(context.test_files)),
            AgentMetric(name="config_files", value=len(context.config_files)),
        ]
        summary = "Reviewed project structure, engineering hygiene and test readiness."
        return findings, metrics, summary
