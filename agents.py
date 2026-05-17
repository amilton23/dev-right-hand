# agents.py
# Definição dos agentes CrewAI para pipeline de laudos AP
# Hapvida Nosso Saúde — Oncologia

from crewai import Agent
from crewai_tools import FileReadTool
from langchain_anthropic import ChatAnthropic
from caveman_prompt import apply_caveman

# ─────────────────────────────────────────────
# LLM Base — Claude Sonnet 4 via Anthropic API
# ─────────────────────────────────────────────
claude_sonnet = ChatAnthropic(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,       # baixo = menos tokens de output = menor custo
    temperature=0.0,       # determinístico para laudos médicos
)

# ─────────────────────────────────────────────
# AGENTE 1: Extrator de Entidades Clínicas
# Responsabilidade única: NER no texto do laudo
# ─────────────────────────────────────────────
extractor_backstory = apply_caveman(
    """
    You are a clinical NER specialist. Extract from anatomopathological reports:
    - topography (organ/tissue)
    - morphology (histological type)
    - staging indicators (TNM fragments if present)
    - IHQ markers
    - laterality
    Output strict JSON. No inference. Only what is explicitly stated.
    """,
    mode="inter_agent"  # Caveman máximo: só JSON, sem prosa
)

extractor_agent = Agent(
    role="Clinical Entity Extractor",
    goal=(
        "Extract structured clinical entities from raw AP report text. "
        "Return only a JSON object with keys: topography, morphology, "
        "staging, ihq_markers, laterality, confidence_score."
    ),
    backstory=extractor_backstory,
    llm=claude_sonnet,
    verbose=False,          # silencia logs do agente
    allow_delegation=False, # agente folha — não delega
    max_iter=2,             # limita retries → menos tokens gastos
)

# ─────────────────────────────────────────────
# AGENTE 2: Classificador CID-O / CID-10
# Responsabilidade única: mapear entidades → código
# ─────────────────────────────────────────────
classifier_backstory = apply_caveman(
    """
    You are an oncology coding specialist (CID-O 3.2 and CID-10).
    Given structured clinical entities, return the best-fit CID-O morphology code,
    CID-O topography code, and CID-10 equivalent.
    If ambiguous, return top 2 candidates with confidence scores.
    Output strict JSON only.
    """,
    mode="inter_agent"
)

classifier_agent = Agent(
    role="Oncology Code Classifier",
    goal=(
        "Map extracted clinical entities to CID-O 3.2 morphology/topography codes "
        "and CID-10. Return JSON: {cid_o_morph, cid_o_topo, cid_10, confidence, alternatives}."
    ),
    backstory=classifier_backstory,
    llm=claude_sonnet,
    verbose=False,
    allow_delegation=False,
    max_iter=2,
)

# ─────────────────────────────────────────────
# AGENTE 3: Detector de Alertas Clínicos
# Responsabilidade única: flags de urgência e SSI risk
# ─────────────────────────────────────────────
alert_backstory = apply_caveman(
    """
    You are a clinical alert specialist for oncology and surgical workflows.
    Given classified report data, identify:
    - Urgency flags (high-grade malignancy, margin involvement, lymphovascular invasion)
    - SSI risk indicators (immunosuppression markers, specific tumor types pre-surgery)
    - Missing critical information that requires pathologist review
    Output JSON with severity: critical | high | medium | low.
    """,
    mode="inter_agent"
)

alert_agent = Agent(
    role="Clinical Alert Detector",
    goal=(
        "Identify urgency flags, SSI risk indicators, and data gaps from classified AP report. "
        "Return JSON: {alerts: [{type, severity, description}], ssi_risk_score, requires_review}."
    ),
    backstory=alert_backstory,
    llm=claude_sonnet,
    verbose=False,
    allow_delegation=False,
    max_iter=2,
)

# ─────────────────────────────────────────────
# AGENTE 4: Sintetizador de Relatório Final
# Único agente com output em prosa (para o médico)
# Usa Caveman "full" (não inter_agent) — output legível
# ─────────────────────────────────────────────
synthesizer_backstory = apply_caveman(
    """
    You are a senior pathology report synthesizer for Hapvida clinical teams.
    Given entities, codes, and alerts from upstream agents, produce a concise
    structured clinical summary in Portuguese (Brazil).
    Format: short sections only — Diagnóstico, Codificação, Alertas, Próximos Passos.
    No redundancy. No filler. Clinicians are busy.
    """,
    mode="full"  # Caveman moderado: sem filler, mas prosa legível
)

synthesizer_agent = Agent(
    role="Clinical Report Synthesizer",
    goal=(
        "Produce a concise structured clinical summary in PT-BR for the medical team, "
        "incorporating all upstream agent outputs. Sections: Diagnóstico, Codificação, "
        "Alertas, Próximos Passos."
    ),
    backstory=synthesizer_backstory,
    llm=claude_sonnet,
    verbose=True,   # único agente com verbose=True → útil para auditoria
    allow_delegation=False,
    max_iter=3,
)
