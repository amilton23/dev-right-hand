# Architecture

## Overview

The project follows a modular architecture built around specialized agents. Each agent operates on a `RepositoryContext`, emits structured findings through `Finding`, and produces an `AgentReport`. The `MultiAgentOrchestrator` coordinates execution, and the `ExecutionTracker` provides end-to-end traceability.

## Core Components

### 1. CLI

Responsible for:

- receiving the target directory;
- loading configuration;
- starting the orchestrator;
- serializing the final report.

### 2. Typed Contracts

All components share Pydantic models for:

- severity;
- finding category;
- recommendation;
- agent metrics;
- repository context;
- execution summary.

This makes future integration with APIs, queues, and databases much easier.

### 3. Specialized Agents

Each agent inherits from `BaseAgent` and implements only the analysis logic for its own domain.

Responsibilities:

- `CodeReviewAgent`: software engineering and testing.
- `DataQualityAgent`: data quality, contracts, and data risk.
- `MLValidationAgent`: training, metrics, and drift.
- `LLMSafetyAgent`: guardrails and agent/LLM safety.
- `ObservabilityAgent`: logs, metrics, alerts, and operational readiness.

### 4. Orchestrator

O `MultiAgentOrchestrator`:

- discovers relevant files;
- builds the shared context;
- executes agents in sequence;
- captures failures without bringing down the full execution;
- produces a `RepositoryAnalysisReport`.

### 5. Tracking

O `ExecutionTracker` registra:

- `run_id`;
- start and finish timestamps;
- duration per agent;
- status;
- number of findings;
- aggregated severity.

Today, tracking is in-memory with structured logging. It can later be adapted to MLflow, OpenTelemetry, Datadog, Langfuse, or a relational database.

## Design Principles

- YAGNI: start with simple heuristics before integrating heavy tooling.
- SOLID: agents have clear responsibilities and depend on stable contracts.
- Extensibility: new agents can be added without changing the rest of the foundation.
- Fail-soft: one agent failure should not interrupt the full analysis.
- Observability from day one.

## Suggested Evolution

### Static Analysis Layer

- `ruff`
- `mypy`
- `bandit`
- `pytest --cov`

### Data Layer

- Great Expectations
- Soda
- dbt tests

### ML Layer

- MLflow
- Evidently
- WhyLabs

### LLMOps Layer

- prompt registry
- eval suites
- red teaming
- groundedness checks
- cost and latency dashboards
