from __future__ import annotations

from dev_right_hand.agents.base import BaseAgent
from dev_right_hand.contracts import AgentMetric, Finding, FindingCategory, RepositoryContext, Severity


class LLMSafetyAgent(BaseAgent):
    name = "LLMSafetyAgent"

    def analyze(
        self, context: RepositoryContext
    ) -> tuple[list[Finding], list[AgentMetric], str]:
        findings: list[Finding] = []
        llm_related = [
            path
            for path in context.python_files
            if any(token in path.name.lower() for token in ("agent", "prompt", "llm", "rag"))
        ]

        if llm_related and not any(path.name.endswith(("yaml", "yml", "json")) for path in context.config_files):
            findings.append(
                Finding(
                    agent_name=self.name,
                    category=FindingCategory.LLM_SAFETY,
                    severity=Severity.MEDIUM,
                    title="Prompt and policy configuration not detected",
                    description="LLM-related modules exist but no obvious policy/config files were found.",
                    recommendation="Version prompts, tool policies and evaluation configs outside application code.",
                )
            )

        if llm_related:
            findings.append(
                Finding(
                    agent_name=self.name,
                    category=FindingCategory.LLM_SAFETY,
                    severity=Severity.MEDIUM,
                    title="Guardrail checks should be formalized",
                    description="Projects with agentic workflows benefit from explicit hallucination and drift tests.",
                    recommendation=(
                        "Add evaluation suites for groundedness, prompt injection, scope drift and unsafe tool usage."
                    ),
                )
            )

        metrics = [
            AgentMetric(name="llm_related_files", value=len(llm_related)),
        ]
        summary = "Reviewed repository readiness for guardrails, prompt governance and agent safety checks."
        return findings, metrics, summary
