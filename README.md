# dev-right-hand

Python multi-agent platform to analyze repositories and data pipelines with professional tracking, engineering best practices, and evaluation workflows for Data Scientists, Data Engineers, ML Engineers, and AI Engineers.

## Goals

- Analyze source code from a folder or repository.
- Identify improvement opportunities in software engineering, data quality, ML, and AI systems.
- Standardize observability and execution tracking across agents.
- Support incremental evolution toward real integrations with Git, CI/CD, registries, warehouses, and experiment tracking platforms.

## Initial Agents

- `CodeReviewAgent`: formatting, YAGNI, SOLID, coupling, readability, and test coverage.
- `DataQualityAgent`: schema checks, nulls, duplicates, ranges, and training-data risk.
- `MLValidationAgent`: baselines, reproducibility, drift, minimum metrics, and training readiness.
- `LLMSafetyAgent`: guardrails, prompt injection, scope drift, unsafe tool usage, and prompt traceability.
- `ObservabilityAgent`: logs, metrics, traces, alerts, SLAs, and operational readiness.

## Initial Stack

- Python 3.11+
- `pydantic` for typed contracts
- `typer` for the CLI
- `structlog` for structured logging
- `pytest` for tests
- `ruff` for linting and formatting

## Structure

```text
.
├── LICENSE
├── README.md
├── docs
│   ├── architecture.md
│   └── roadmap.md
├── pyproject.toml
├── setup.py
├── src
│   └── dev_right_hand
│       ├── agents
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── code_review.py
│       │   ├── data_quality.py
│       │   ├── llm_safety.py
│       │   ├── ml_validation.py
│       │   └── observability.py
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── contracts.py
│       ├── orchestrator.py
│       └── tracking.py
└── tests
    ├── test_agents.py
    ├── test_orchestrator.py
    └── test_tracking.py
```

## How To Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
dev-right-hand scan .
```

## Current Flow

1. The CLI receives a target directory.
2. The orchestrator builds a shared execution context.
3. Each agent runs a local analysis based on initial heuristics.
4. The tracker records start time, finish time, duration, severity, and recommendations.
5. A consolidated report is printed as JSON.

## Practical Implementation Guide

This section is meant for a developer who wants to turn the scaffold into a production-ready multi-agent platform.

### 1. Start with one reliable vertical slice

Pick one domain first, usually code review or data quality, and make it trustworthy before adding more agents. A good first slice is:

- one CLI command;
- one agent with clear inputs and outputs;
- one tracking mechanism;
- one JSON report;
- one test suite covering the happy path and one failure path.

This keeps the system simple and aligned with YAGNI.

### 2. Define stable contracts before adding complexity

Use the models in `contracts.py` as the backbone of the system:

- `RepositoryContext` should describe everything an agent needs to inspect.
- `Finding` should remain the standard output for all agents.
- `AgentReport` should remain the unit of accountability per agent.
- `RepositoryAnalysisReport` should remain the final artifact produced by the orchestration layer.

When you add a new agent, prefer extending the context and metadata rather than creating a completely different output shape.

### 3. Implement a new agent in practice

Use this sequence:

1. Create a new agent file in `src/dev_right_hand/agents/`.
2. Inherit from `BaseAgent`.
3. Implement `analyze(context)` and return `findings`, `metrics`, and a short summary.
4. Register the agent in `src/dev_right_hand/agents/__init__.py`.
5. Add the agent to `MultiAgentOrchestrator`.
6. Create tests that validate:
   - when the issue exists;
   - when the issue does not exist;
   - what severity and recommendation are returned.

### 4. Connect the project to real tools

A practical evolution path is:

- Code quality: `ruff`, `mypy`, `bandit`, `pytest --cov`.
- Data quality: Great Expectations, Soda, dbt tests, schema registries.
- ML validation: MLflow, Evidently, WhyLabs, custom regression thresholds.
- LLM safety: prompt registries, eval suites, red teaming, groundedness checks.
- Observability: OpenTelemetry, structured logs, metrics exporters, alert routing.

### 5. Keep the architecture operationally clean

As the project grows:

- keep agents specialized;
- keep orchestration thin;
- keep contracts stable;
- avoid embedding infrastructure logic directly inside agents;
- treat tracking as a first-class concern, not an afterthought.

## How To Track Activities

Tracking should answer four questions:

- What ran?
- When did it run?
- What did it find?
- What should happen next?

### What to track per execution

At minimum, record:

- `run_id`
- target repository or directory
- agent name
- start time
- finish time
- duration
- execution status
- number of findings
- severities found
- recommendations produced

The current `ExecutionTracker` already provides the starting point for this model.

### What to track per finding

Each finding should be traceable enough to support triage and audit:

- category
- severity
- title
- description
- affected file or asset
- recommendation
- metadata such as threshold values, metric snapshots, or rule identifiers

### Recommended tracking layers

Use a layered approach:

1. Structured logs for local development and debugging.
2. JSON reports for deterministic artifacts and CI outputs.
3. Metrics dashboards for aggregate behavior over time.
4. Persistent storage for historical analysis, trends, and compliance evidence.

### Suggested implementation path for tracking

1. Keep the in-memory tracker for the first iteration.
2. Add JSON export to a local `artifacts/` directory.
3. Add an adapter interface for external backends.
4. Integrate with MLflow, OpenTelemetry, Datadog, Langfuse, or a database.
5. Build dashboards for:
   - findings by severity;
   - findings by agent;
   - average execution time;
   - failure rate;
   - drift incidents and threshold breaches.

### Example of a practical tracking workflow

1. A developer runs `dev-right-hand scan ./my-project`.
2. The orchestrator creates a `run_id`.
3. Each agent emits start and finish events.
4. Findings are consolidated into a final report.
5. The report is stored locally or shipped to a tracking backend.
6. A CI job or alerting system reacts if critical findings exceed a threshold.

### Team-level best practices

- Use one `run_id` per full analysis.
- Use one `AgentReport` per agent execution.
- Keep finding severities standardized across the whole project.
- Version prompts, rules, thresholds, and agent configurations.
- Treat tracking artifacts as part of the engineering evidence of the system.

## Next Steps

- Connect to Git repositories and pull requests.
- Read real coverage outputs, test logs, and training artifacts.
- Integrate with MLflow, OpenTelemetry, Great Expectations, and Evidently.
- Add asynchronous agents and parallel execution pipelines.
- Persist executions in a database and observability dashboard.

## Documentation

- [Architecture](docs/architecture.md)
- [Roadmap](docs/roadmap.md)
