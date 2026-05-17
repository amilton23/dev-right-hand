# crew.py
# Definição das Tasks e montagem da Crew
# Pipeline sequencial com passagem de contexto entre agentes

from crewai import Task, Crew, Process
from agents import extractor_agent, classifier_agent, alert_agent, synthesizer_agent

# ─────────────────────────────────────────────
# TASK 1: Extração de Entidades
# Input: texto bruto do laudo
# Output: JSON de entidades clínicas
# ─────────────────────────────────────────────
task_extract = Task(
    description=(
        "Extract all clinical entities from the following AP report text:\n\n"
        "{report_text}\n\n"
        "Return only a JSON object. No prose."
    ),
    expected_output=(
        "JSON with keys: topography, morphology, staging, ihq_markers, "
        "laterality, confidence_score (0.0–1.0)."
    ),
    agent=extractor_agent,
    # Sem context — é a primeira task, recebe input direto
)

# ─────────────────────────────────────────────
# TASK 2: Classificação CID-O / CID-10
# Input: output da Task 1 (via context)
# Output: JSON de códigos
# ─────────────────────────────────────────────
task_classify = Task(
    description=(
        "Using the extracted clinical entities from the previous task, "
        "map to the most accurate CID-O 3.2 morphology code, topography code, "
        "and CID-10 equivalent. Return JSON only."
    ),
    expected_output=(
        "JSON with keys: cid_o_morph, cid_o_topo, cid_10, confidence (0.0–1.0), "
        "alternatives (list of up to 2 alternate codes with confidence)."
    ),
    agent=classifier_agent,
    context=[task_extract],  # recebe output da task anterior
)

# ─────────────────────────────────────────────
# TASK 3: Detecção de Alertas
# Input: outputs das Tasks 1 e 2 (via context)
# Output: JSON de alertas e risk scores
# ─────────────────────────────────────────────
task_alert = Task(
    description=(
        "Using the extracted entities and classification codes from previous tasks, "
        "identify all clinical alert flags, SSI risk indicators, and data gaps. "
        "Return JSON only."
    ),
    expected_output=(
        "JSON with keys: alerts (list of {type, severity, description}), "
        "ssi_risk_score (0–10), requires_review (bool), review_reason (str or null)."
    ),
    agent=alert_agent,
    context=[task_extract, task_classify],
)

# ─────────────────────────────────────────────
# TASK 4: Síntese Final
# Input: outputs de todas as tasks anteriores
# Output: relatório clínico estruturado em PT-BR
# ─────────────────────────────────────────────
task_synthesize = Task(
    description=(
        "Synthesize all previous task outputs into a concise structured clinical "
        "summary in Brazilian Portuguese for the medical team at Hapvida. "
        "Use sections: Diagnóstico, Codificação, Alertas, Próximos Passos. "
        "Be direct. Clinicians are busy."
    ),
    expected_output=(
        "Structured clinical summary in PT-BR with 4 sections: "
        "Diagnóstico, Codificação, Alertas, Próximos Passos. "
        "Max 300 words."
    ),
    agent=synthesizer_agent,
    context=[task_extract, task_classify, task_alert],
)

# ─────────────────────────────────────────────
# CREW — Pipeline Sequencial
# Process.sequential = cada task espera a anterior
# memory=False → sem persistência entre runs (LGPD-safe)
# ─────────────────────────────────────────────
ap_analysis_crew = Crew(
    agents=[extractor_agent, classifier_agent, alert_agent, synthesizer_agent],
    tasks=[task_extract, task_classify, task_alert, task_synthesize],
    process=Process.sequential,
    verbose=True,
    memory=False,           # desabilitado por padrão — dados de paciente
    output_log_file="logs/crew_run.log",
)
