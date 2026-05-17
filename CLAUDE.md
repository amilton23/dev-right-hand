# CLAUDE.md — Hapvida AP Pipeline
# Formato: caveman-compress (prosa removida, estrutura preservada)

## Project
AP report analysis pipeline. CrewAI + Claude Sonnet 4 + Caveman token compression.
4 sequential agents: Extract → Classify → Alert → Synthesize.

## Stack
- crewai>=0.63.0
- langchain-anthropic>=0.3.0
- anthropic>=0.40.0
- python>=3.11

## Key files
- agents.py → 4 Agent definitions (extractor, classifier, alert, synthesizer)
- crew.py → Task wiring + Crew assembly (Process.sequential)
- caveman_prompt.py → Token compression system prompts (full + inter_agent modes)
- main.py → Entrypoint + TokenMonitor + sample laudo

## Rules
- memory=False on Crew (LGPD compliance)
- max_iter=2 on leaf agents, 3 on synthesizer
- verbose=False on all except synthesizer (audit trail)
- temperature=0.0 (deterministic outputs for medical data)
- Caveman inter_agent mode on agents 1-3, full mode on agent 4 only
- All logs → logs/ directory (gitignored)

## Run
```bash
python main.py
```

## Token budget (baseline — sem Caveman)
~4800 tokens/run (4 agents × ~1200 avg)
## Token budget (com Caveman inter_agent)
~1800 tokens/run (estimado ~62% redução nos agentes 1-3)

## Extend
Add new agent → define in agents.py → add Task in crew.py → append to context list of synthesizer task.
