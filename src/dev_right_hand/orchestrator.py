from __future__ import annotations

from pathlib import Path

from dev_right_hand.agents import (
    CodeReviewAgent,
    DataQualityAgent,
    LLMSafetyAgent,
    MLValidationAgent,
    ObservabilityAgent,
)
from dev_right_hand.agents.base import BaseAgent
from dev_right_hand.config import AppConfig
from dev_right_hand.contracts import AgentReport, RepositoryAnalysisReport, RepositoryContext
from dev_right_hand.tracking import ExecutionTracker


class MultiAgentOrchestrator:
    def __init__(self, config: AppConfig, agents: list[BaseAgent] | None = None) -> None:
        self.config = config
        self.tracker = ExecutionTracker()
        self.agents = agents or [
            CodeReviewAgent(),
            DataQualityAgent(),
            MLValidationAgent(),
            LLMSafetyAgent(),
            ObservabilityAgent(),
        ]

    def build_context(self) -> RepositoryContext:
        root = self.config.repository_root
        python_files = sorted(root.rglob("*.py"))
        test_files = [path for path in python_files if "test" in path.name.lower() or "tests" in path.parts]
        config_files = sorted(
            [
                *root.glob("pyproject.toml"),
                *root.rglob("*.yaml"),
                *root.rglob("*.yml"),
                *root.rglob("*.json"),
                *root.rglob("*.toml"),
            ]
        )
        model_files = [
            path
            for path in python_files
            if any(token in path.name.lower() for token in ("model", "train", "predict"))
        ]

        return RepositoryContext(
            repository_root=root,
            python_files=python_files,
            test_files=test_files,
            config_files=config_files,
            model_files=model_files,
        )

    def analyze(self) -> RepositoryAnalysisReport:
        context = self.build_context()
        reports: list[AgentReport] = []

        for agent in self.agents:
            self.tracker.record(agent.name, "started")
            report = agent.run(context)
            reports.append(report)
            self.tracker.record(
                agent.name,
                "finished" if report.succeeded else "failed",
                findings=len(report.findings),
                summary=report.summary,
            )

        return RepositoryAnalysisReport(
            run_id=self.tracker.run_id,
            repository_root=context.repository_root,
            agent_reports=reports,
        )
