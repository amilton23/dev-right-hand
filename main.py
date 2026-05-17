# main.py
# Entrypoint do pipeline — com monitoramento de tokens e laudo de exemplo

import json
import time
from crew import ap_analysis_crew

# ─────────────────────────────────────────────
# Laudo AP de exemplo (anonimizado / fictício)
# Representa o tipo de input que chega do HIS
# ─────────────────────────────────────────────
SAMPLE_REPORT = """
LAUDO ANATOMOPATOLÓGICO

Material: Peça cirúrgica — mastectomia radical modificada à direita.
Procedimento: Mastectomia radical modificada + esvaziamento axilar.

MACROSCOPIA:
Mama direita pesando 420g, medindo 18x14x6 cm. Ao corte, observa-se nódulo 
mal delimitado, de consistência endurecida, medindo 3,2 x 2,8 x 2,1 cm, 
localizado no quadrante superior externo, a 1,5 cm da margem cirúrgica mais 
próxima (margem axilar). Pele e complexo areolopapilar sem alterações 
macroscópicas evidentes. Linfonodos axilares: 18 identificados.

MICROSCOPIA:
Carcinoma ductal invasivo, grau histológico III (Nottingham: 3+3+3=9).
Invasão angiolinfática presente. Invasão perineural ausente.
Margem axilar comprometida por neoplasia.
Linfonodos: 4/18 com metástase, com extensão extracapsular em 1 linfonodo.

IMUNOHISTOQUÍMICA:
RE: negativo (0%)
RP: negativo (0%)
HER2: 3+ (positivo)
Ki-67: 78%
CK5/6: negativo

CONCLUSÃO:
Carcinoma ductal invasivo de mama direita, grau III, subtipo molecular HER2-enriched.
pT2 pN2a (4/18) M0 — Estádio IIIA.
Margem axilar positiva. Indicada discussão em tumor board.
"""

# ─────────────────────────────────────────────
# Token Monitor — mede consumo antes/depois
# Útil para validar ganho do Caveman
# ─────────────────────────────────────────────
class TokenMonitor:
    def __init__(self):
        self.start_time = None
        self.runs = []

    def start(self):
        self.start_time = time.time()
        print("\n" + "─"*60)
        print("🔬 PIPELINE AP — INICIANDO")
        print("─"*60)

    def finish(self, result, token_usage: dict = None):
        elapsed = time.time() - self.start_time
        run_data = {
            "elapsed_seconds": round(elapsed, 2),
            "token_usage": token_usage or {},
        }
        self.runs.append(run_data)
        
        print("\n" + "─"*60)
        print(f"✅ PIPELINE CONCLUÍDO em {elapsed:.1f}s")
        if token_usage:
            total = token_usage.get("total_tokens", "N/A")
            input_t = token_usage.get("input_tokens", "N/A")
            output_t = token_usage.get("output_tokens", "N/A")
            print(f"📊 Tokens — Input: {input_t} | Output: {output_t} | Total: {total}")
        print("─"*60 + "\n")
        return run_data

monitor = TokenMonitor()

# ─────────────────────────────────────────────
# Execução do Pipeline
# ─────────────────────────────────────────────
def run_ap_pipeline(report_text: str) -> dict:
    """
    Executa o pipeline completo de análise de laudo AP.
    
    Args:
        report_text: Texto bruto do laudo anatomopatológico
    
    Returns:
        dict com resultado final e métricas de execução
    """
    monitor.start()
    
    inputs = {"report_text": report_text}
    
    # Kickoff da Crew — sequencial, cada agente passa o contexto para o próximo
    result = ap_analysis_crew.kickoff(inputs=inputs)
    
    # CrewAI expõe uso de tokens via result.token_usage (crewai >= 0.63)
    token_usage = {}
    if hasattr(result, "token_usage") and result.token_usage:
        token_usage = {
            "input_tokens": result.token_usage.prompt_tokens,
            "output_tokens": result.token_usage.completion_tokens,
            "total_tokens": result.token_usage.total_tokens,
        }
    
    run_data = monitor.finish(result, token_usage)
    
    return {
        "final_report": result.raw,
        "metrics": run_data,
    }


if __name__ == "__main__":
    output = run_ap_pipeline(SAMPLE_REPORT)
    
    print("═"*60)
    print("RELATÓRIO CLÍNICO FINAL")
    print("═"*60)
    print(output["final_report"])
    print("\n")
    
    # Salva resultado em JSON para auditoria / ingestão no Delta Lake
    with open("logs/last_run_output.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print("📁 Output salvo em logs/last_run_output.json")
