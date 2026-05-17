# Referência técnica dos arquivos Python

Este documento descreve a funcionalidade técnica de cada arquivo `.py` do repositório `dev-right-hand`, com referências internas para os principais pontos de implementação.

## Visão geral

O repositório contém dois conjuntos Python distintos:

1. **Pacote `dev_right_hand`**, em `src/dev_right_hand/`, que implementa uma plataforma multiagente local para analisar repositórios Python e produzir relatórios estruturados.
2. **Protótipo CrewAI na raiz**, composto por `agents.py`, `crew.py`, `main.py` e `caveman_prompt.py`, que modela um pipeline médico para análise de laudos anatomopatologicos.

O pacote instalável e exposto pelo `pyproject.toml` como comando `dev-right-hand`, apontando para `dev_right_hand.cli:app`. O arquivo `setup.py` existe como shim minimo para o `setuptools`.

## Fluxo principal do pacote `dev_right_hand`

1. `src/dev_right_hand/cli.py` recebe um diretorio via comando `scan`.
2. `src/dev_right_hand/config.py` cria um `AppConfig` com o caminho raiz do repositório.
3. `src/dev_right_hand/orchestrator.py` monta um `RepositoryContext` a partir dos arquivos encontrados.
4. O orquestrador executa cinco agentes especializados:
   - `CodeReviewAgent`
   - `DataQualityAgent`
   - `MLValidationAgent`
   - `LLMSafetyAgent`
   - `ObservabilityAgent`
5. Cada agente herda de `BaseAgent` e retorna `AgentReport`.
6. `ExecutionTracker` registra eventos de inicio e fim por agente.
7. O resultado consolidado e impresso como JSON por `cli.py`.

Referencias principais:

- `src/dev_right_hand/cli.py:16` define o comando `scan`.
- `src/dev_right_hand/orchestrator.py:30` monta o contexto do repositório.
- `src/dev_right_hand/orchestrator.py:57` executa os agentes.
- `src/dev_right_hand/contracts.py:76` define o relatorio consolidado.
- `src/dev_right_hand/tracking.py:26` registra eventos de execucao.

## Arquivos da raiz

### `setup.py`

Arquivo minimo de compatibilidade com `setuptools`.

Funcionalidade:

- Importa `setup` de `setuptools`.
- Executa `setup()` sem parametros explicitos.
- Delega metadados de build e empacotamento ao `pyproject.toml`.

Uso tecnico:

- Mantem suporte a fluxos que ainda esperam `setup.py`.
- Nao contém regras de negocio.
- Nao declara Dependências, entry points ou pacotes diretamente.

Referência:

- `setup.py:1` importa `setup`.
- `setup.py:4` executa `setup()`.

### `caveman_prompt.py`

Define prompts de sistema para reduzir verbosidade em agentes CrewAI.

Funcionalidade:

- Declara `CAVEMAN_SYSTEM`, prompt de estilo "full", voltado a respostas concisas para usuario ou saidas finais.
- Declara `CAVEMAN_INTER_AGENT`, prompt mais restritivo para comunicacao entre agentes, exigindo JSON e evitando prosa.
- Fornece `apply_caveman(base_system_prompt, mode="full")`, helper que injeta o prompt Caveman antes do prompt especifico de um agente.

Comportamento tecnico:

- Se `mode == "inter_agent"`, usa `CAVEMAN_INTER_AGENT`.
- Para qualquer outro valor, usa `CAVEMAN_SYSTEM`.
- Retorna uma string composta por prefixo Caveman, separador `---` e prompt original.

Dependências:

- Nao depende de bibliotecas externas.
- E consumido por `agents.py`.

Referências:

- `caveman_prompt.py:5` define `CAVEMAN_SYSTEM`.
- `caveman_prompt.py:20` define `CAVEMAN_INTER_AGENT`.
- `caveman_prompt.py:26` define `apply_caveman`.
- `agents.py:23`, `agents.py:54`, `agents.py:82` e `agents.py:112` usam `apply_caveman`.

### `agents.py`

Define quatro agentes CrewAI para o pipeline médico de laudos AP.

Funcionalidade:

- Configura um LLM base `claude_sonnet` usando `ChatAnthropic`.
- Define backstories e agentes para:
  - extracao de entidades clinicas;
  - classificacao CID-O/CID-10;
  - deteccao de alertas clinicos;
  - sintese final em portugues brasileiro.

Componentes:

- `claude_sonnet`: instancia `ChatAnthropic` com modelo `claude-sonnet-4-20250514`, `temperature=0.0` e limite de `1024` tokens.
- `extractor_agent`: agente de NER clinico, focado em topografia, morfologia, estadiamento, marcadores IHQ, lateralidade e confianca.
- `classifier_agent`: agente de codificacao oncologica, mapeando entidades para CID-O 3.2 e CID-10.
- `alert_agent`: agente de flags clinicas e risco SSI.
- `synthesizer_agent`: agente final, responsavel por gerar resumo clinico estruturado em PT-BR.

Comportamento tecnico:

- Os tres primeiros agentes usam modo `inter_agent`, que favorece JSON estrito.
- O sintetizador usa modo `full`, permitindo prosa curta.
- Todos os agentes têm `allow_delegation=False`, indicando agentes folha (finais).
- Os agentes intermediarios têm `verbose=False`; o sintetizador usa `verbose=True` para auditoria.
- `FileReadTool` é importado, mas não é utilizado no arquivo atual.

Dependências:

- `crewai.Agent`
- `crewai_tools.FileReadTool`
- `langchain_anthropic.ChatAnthropic`
- `caveman_prompt.apply_caveman`

Referências:

- `agents.py:13` configura `claude_sonnet`.
- `agents.py:23` cria `extractor_backstory`.
- `agents.py:36` define `extractor_agent`.
- `agents.py:54` cria `classifier_backstory`.
- `agents.py:65` define `classifier_agent`.
- `agents.py:82` cria `alert_backstory`.
- `agents.py:94` define `alert_agent`.
- `agents.py:112` cria `synthesizer_backstory`.
- `agents.py:123` define `synthesizer_agent`.

### `crew.py`

Monta as tarefas e a `Crew` sequencial do pipeline médico.

Funcionalidade:

- Define quatro `Task` sequenciais:
  - `task_extract`
  - `task_classify`
  - `task_alert`
  - `task_synthesize`
- Encadeia outputs via `context`, permitindo que cada etapa use o resultado das anteriores.
- Cria `ap_analysis_crew` com `Process.sequential`.

Comportamento tecnico:

- `task_extract` recebe `{report_text}` diretamente no prompt e deve retornar JSON de entidades clinicas.
- `task_classify` depende de `task_extract` e retorna codigos CID-O/CID-10.
- `task_alert` depende de `task_extract` e `task_classify`, retornando alertas e score de risco SSI.
- `task_synthesize` depende das tres tarefas anteriores e produz resumo estruturado em PT-BR.
- `memory=False` evita persistencia entre execucoes, escolha relevante para dados sensiveis.
- `output_log_file="logs/crew_run.log"` direciona logs para arquivo.

Dependências:

- `crewai.Task`
- `crewai.Crew`
- `crewai.Process`
- Agentes definidos em `agents.py`

Referências:

- `crew.py:13` define `task_extract`.
- `crew.py:32` define `task_classify`.
- `crew.py:51` define `task_alert`.
- `crew.py:70` define `task_synthesize`.
- `crew.py:91` define `ap_analysis_crew`.

### `main.py`

Entrypoint executavel do prototipo médico CrewAI.

Funcionalidade:

- Define `SAMPLE_REPORT`, laudo anatomopatologico ficticio e anonimizado.
- Implementa `TokenMonitor`, utilitario simples para medir tempo e tokens.
- Implementa `run_ap_pipeline(report_text)`, que executa `ap_analysis_crew`.
- Quando executado diretamente, roda o pipeline com `SAMPLE_REPORT`, imprime o relatorio final e salva JSON em `logs/last_run_output.json`.

Componentes:

- `SAMPLE_REPORT`: texto de exemplo com macro, micro, IHQ e conclusao.
- `TokenMonitor.start()`: imprime cabecalho de inicio e armazena timestamp.
- `TokenMonitor.finish()`: calcula duracao, registra metricas e imprime resumo.
- `run_ap_pipeline()`: faz `kickoff` da crew, extrai `token_usage` quando disponivel e retorna dicionario com `final_report` e `metrics`.

Comportamento tecnico:

- Usa `result.raw` como relatorio final.
- Assume que `logs/` existe antes de salvar o JSON; caso contrario, a escrita pode falhar.
- Usa `hasattr(result, "token_usage")` para manter compatibilidade com versoes do CrewAI que exponham ou nao metricas.

Dependências:

- `json`
- `time`
- `crew.ap_analysis_crew`

Referências:

- `main.py:12` define `SAMPLE_REPORT`.
- `main.py:48` define `TokenMonitor`.
- `main.py:49` inicializa estado do monitor.
- `main.py:53` inicia medicao.
- `main.py:59` finaliza medicao.
- `main.py:77` instancia `monitor`.
- `main.py:82` define `run_ap_pipeline`.
- `main.py:116` executa o fluxo quando chamado como script.

## Pacote `src/dev_right_hand`

### `src/dev_right_hand/__init__.py`

Define a API publica minima do pacote.

Funcionalidade:

- Importa `MultiAgentOrchestrator`.
- Expõe `MultiAgentOrchestrator` via `__all__`.

Uso tecnico:

- Permite `from dev_right_hand import MultiAgentOrchestrator`.
- Mantem a superficie publica do pacote pequena e explicita.

Referências:

- `src/dev_right_hand/__init__.py:3` importa o orquestrador.
- `src/dev_right_hand/__init__.py:5` define `__all__`.

### `src/dev_right_hand/config.py`

Define configuracoes tipadas da aplicacao usando Pydantic.

Modelos:

- `TrackingSettings`
  - `enabled: bool = True`
  - `sink: str = "stdout"`
- `ThresholdSettings`
  - `min_test_files: int = 1`
  - `min_training_files: int = 1`
  - `max_critical_findings: int = 0`
- `AppConfig`
  - `repository_root: Path`
  - `tracking: TrackingSettings`
  - `thresholds: ThresholdSettings`

Funcionalidade:

- Centraliza parametros de execucao.
- Usa `Field(default_factory=...)` para evitar defaults mutaveis e instanciar subconfiguracoes de forma segura.
- Serve como entrada principal para `MultiAgentOrchestrator`.

Referências:

- `src/dev_right_hand/config.py:8` define `TrackingSettings`.
- `src/dev_right_hand/config.py:13` define `ThresholdSettings`.
- `src/dev_right_hand/config.py:19` define `AppConfig`.
- `src/dev_right_hand/cli.py:18` cria `AppConfig` com `repository_root`.
- `src/dev_right_hand/orchestrator.py:19` recebe `AppConfig`.

### `src/dev_right_hand/contracts.py`

Define os contratos de dados compartilhados por CLI, orquestrador, agentes e tracker.

Enums:

- `StringEnum`: base `str, Enum` para manter enums serializaveis como strings.
- `Severity`: niveis `info`, `low`, `medium`, `high`, `critical`.
- `FindingCategory`: categorias `code_quality`, `data_quality`, `ml_validation`, `llm_safety`, `observability`.

Modelos Pydantic:

- `Finding`: achado individual produzido por agentes.
- `AgentMetric`: metrica simples de agente, com nome, valor e unidade opcional.
- `RepositoryContext`: contexto compartilhado do repositório analisado.
- `AgentReport`: resultado de uma execucao de agente.
- `ExecutionEvent`: evento emitido pelo tracker.
- `RepositoryAnalysisReport`: relatorio consolidado da análise.

Campos importantes:

- `Finding.file_path` e opcional, permitindo achados globais ou achados ligados a arquivos.
- `Finding.metadata` usa `default_factory=dict` para dados extras rastreaveis.
- `RepositoryContext.created_at` usa `datetime.utcnow`.
- `AgentReport.succeeded` permite representar falha controlada de agente.
- `RepositoryAnalysisReport.findings` agrega todos os achados dos `agent_reports`.

Referências:

- `src/dev_right_hand/contracts.py:11` define `StringEnum`.
- `src/dev_right_hand/contracts.py:15` define `Severity`.
- `src/dev_right_hand/contracts.py:23` define `FindingCategory`.
- `src/dev_right_hand/contracts.py:31` define `Finding`.
- `src/dev_right_hand/contracts.py:42` define `AgentMetric`.
- `src/dev_right_hand/contracts.py:48` define `RepositoryContext`.
- `src/dev_right_hand/contracts.py:57` define `AgentReport`.
- `src/dev_right_hand/contracts.py:68` define `ExecutionEvent`.
- `src/dev_right_hand/contracts.py:76` define `RepositoryAnalysisReport`.
- `src/dev_right_hand/contracts.py:83` agrega findings consolidados.

### `src/dev_right_hand/orchestrator.py`

Implementa o orquestrador multiagente do pacote.

Funcionalidade:

- Recebe `AppConfig`.
- Cria um `ExecutionTracker`.
- Instancia agentes padrao quando uma lista customizada nao e fornecida.
- Constrói `RepositoryContext`.
- Executa agentes em sequencia e consolida `RepositoryAnalysisReport`.

Agentes padrao:

- `CodeReviewAgent`
- `DataQualityAgent`
- `MLValidationAgent`
- `LLMSafetyAgent`
- `ObservabilityAgent`

`build_context()`:

- Usa `root.rglob("*.py")` para localizar arquivos Python.
- Identifica testes quando o nome contém `test` ou quando `tests` aparece em `path.parts`.
- Coleta configs `pyproject.toml`, `*.yaml`, `*.yml`, `*.json`, `*.toml`.
- Identifica `model_files` quando o nome contém `model`, `train` ou `predict`.

`analyze()`:

- Registra evento `started` antes de cada agente.
- Executa `agent.run(context)`.
- Registra `finished` ou `failed` conforme `report.succeeded`.
- Inclui contagem de findings e summary nos detalhes do evento.
- Retorna `RepositoryAnalysisReport` com `run_id`, raiz e relatórios de agentes.

Referências:

- `src/dev_right_hand/orchestrator.py:18` define `MultiAgentOrchestrator`.
- `src/dev_right_hand/orchestrator.py:19` inicializa config, tracker e agentes.
- `src/dev_right_hand/orchestrator.py:30` define `build_context`.
- `src/dev_right_hand/orchestrator.py:32` coleta arquivos Python.
- `src/dev_right_hand/orchestrator.py:33` identifica arquivos de teste.
- `src/dev_right_hand/orchestrator.py:34` coleta arquivos de configuracao.
- `src/dev_right_hand/orchestrator.py:43` identifica arquivos relacionados a modelos.
- `src/dev_right_hand/orchestrator.py:57` define `analyze`.
- `src/dev_right_hand/orchestrator.py:61` registra inicio do agente.
- `src/dev_right_hand/orchestrator.py:62` executa o agente.
- `src/dev_right_hand/orchestrator.py:64` registra termino ou falha.

### `src/dev_right_hand/cli.py`

Define a interface de linha de comando com Typer.

Funcionalidade:

- Cria `app = typer.Typer(...)`.
- Define comando `scan`.
- Valida o argumento `path` como diretorio existente.
- Cria `AppConfig` com `path.resolve()`.
- Executa `MultiAgentOrchestrator`.
- Serializa o relatorio como JSON indentado.

Comportamento tecnico:

- `typer.Argument(..., exists=True, file_okay=False, dir_okay=True)` impede arquivo individual como alvo e exige caminho existente.
- `report.model_dump(mode="json")` usa serializacao Pydantic amigavel a JSON.
- `default=str` no `json.dumps` cobre tipos que ainda precisem de conversao textual.
- O bloco `if __name__ == "__main__"` permite executar o arquivo diretamente.

Referências:

- `src/dev_right_hand/cli.py:12` cria o app Typer.
- `src/dev_right_hand/cli.py:16` define `scan`.
- `src/dev_right_hand/cli.py:18` cria `AppConfig`.
- `src/dev_right_hand/cli.py:19` cria `MultiAgentOrchestrator`.
- `src/dev_right_hand/cli.py:20` executa análise.
- `src/dev_right_hand/cli.py:21` imprime JSON.
- `src/dev_right_hand/cli.py:24` executa app diretamente.

### `src/dev_right_hand/tracking.py`

Implementa rastreamento simples de execucoes em memoria.

Funcionalidade:

- Cria um `run_id` unico por instancia usando `uuid4().hex`.
- Armazena `started_at`.
- Mantem lista privada `_events`.
- Exponibiliza eventos por copia defensiva via property `events`.
- Registra eventos com `record(agent_name, status, **details)`.
- Emite log estruturado com `structlog`.

Comportamento tecnico:

- `events` retorna `list(self._events)`, evitando que consumidores mutem a lista interna diretamente.
- `record` encapsula dados no contrato `ExecutionEvent`.
- Os detalhes variaveis sao convertidos com `dict(details)`.
- O logger envia `agent_event` com `run_id`, `agent_name`, `status` e `details`.

Dependências:

- `datetime.utcnow`
- `uuid4`
- `structlog`
- `ExecutionEvent`

Referências:

- `src/dev_right_hand/tracking.py:11` cria logger.
- `src/dev_right_hand/tracking.py:14` define `ExecutionTracker`.
- `src/dev_right_hand/tracking.py:17` inicializa `run_id`, `started_at` e `_events`.
- `src/dev_right_hand/tracking.py:23` retorna eventos.
- `src/dev_right_hand/tracking.py:26` registra evento.
- `src/dev_right_hand/tracking.py:33` emite log estruturado.

## Pacote `src/dev_right_hand/agents`

### `src/dev_right_hand/agents/__init__.py`

Arquivo de agregacao dos agentes concretos.

Funcionalidade:

- Importa os cinco agentes implementados no pacote.
- Define `__all__` com a lista publica de agentes.

Uso tecnico:

- Permite `from dev_right_hand.agents import CodeReviewAgent, ...`.
- Simplifica imports no orquestrador.

Referências:

- `src/dev_right_hand/agents/__init__.py:1` a `src/dev_right_hand/agents/__init__.py:5` importam agentes.
- `src/dev_right_hand/agents/__init__.py:7` define `__all__`.
- `src/dev_right_hand/orchestrator.py:5` a `src/dev_right_hand/orchestrator.py:11` consomem esses exports.

### `src/dev_right_hand/agents/base.py`

Define a classe abstrata base para todos os agentes.

Funcionalidade:

- Declara atributo `name`.
- Implementa template method `run(context)`.
- Exige implementacao de `analyze(context)` em subclasses.

`run(context)`:

- Marca `started_at`.
- Chama `self.analyze(context)`.
- Empacota retorno em `AgentReport`.
- Captura excecoes de forma defensiva e retorna `AgentReport` com `succeeded=False`.

Contrato de `analyze(context)`:

- Deve retornar uma tupla:
  - `list[Finding]`
  - `list[AgentMetric]`
  - `str` com resumo

Comportamento tecnico:

- A captura ampla de excecoes impede que uma falha individual derrube o orquestrador.
- A anotacao `# pragma: no cover` indica caminho defensivo nao coberto por testes.
- `finished_at` e sempre preenchido, inclusive em falha.

Referências:

- `src/dev_right_hand/agents/base.py:9` define `BaseAgent`.
- `src/dev_right_hand/agents/base.py:12` define `run`.
- `src/dev_right_hand/agents/base.py:16` chama `analyze`.
- `src/dev_right_hand/agents/base.py:17` a `src/dev_right_hand/agents/base.py:24` montam relatorio de sucesso.
- `src/dev_right_hand/agents/base.py:25` a `src/dev_right_hand/agents/base.py:32` montam relatorio de falha.
- `src/dev_right_hand/agents/base.py:35` define metodo abstrato `analyze`.

### `src/dev_right_hand/agents/code_review.py`

Agente de higiene de codigo e estrutura de projeto.

Funcionalidade:

- Avalia sinais basicos de qualidade de codigo Python.
- Verifica se existem arquivos Python.
- Verifica se existem testes.
- Verifica se existe `pyproject.toml`.
- Sinaliza nomes de modulos potencialmente sobrecarregados.
- Retorna metricas de quantidade de arquivos Python, testes e configs.

Regras implementadas:

- Sem arquivos Python: finding `MEDIUM`, categoria `CODE_QUALITY`.
- Arquivos Python sem testes: finding `HIGH`, categoria `CODE_QUALITY`.
- Sem `pyproject.toml`: finding `MEDIUM`.
- Modulos com `stem` maior que 32 caracteres: ate 3 findings `LOW`.

Metricas:

- `python_files`
- `test_files`
- `config_files`

Referências:

- `src/dev_right_hand/agents/code_review.py:9` define `CodeReviewAgent`.
- `src/dev_right_hand/agents/code_review.py:12` implementa `analyze`.
- `src/dev_right_hand/agents/code_review.py:17` detecta ausencia de arquivos Python.
- `src/dev_right_hand/agents/code_review.py:29` detecta ausencia de testes.
- `src/dev_right_hand/agents/code_review.py:41` detecta ausencia de `pyproject.toml`.
- `src/dev_right_hand/agents/code_review.py:53` avalia nomes longos de modulos.
- `src/dev_right_hand/agents/code_review.py:67` define metricas.
- `tests/test_agents.py:7` valida finding de testes ausentes.

### `src/dev_right_hand/agents/data_quality.py`

Agente de sinais de qualidade de dados.

Funcionalidade:

- Procura arquivos de contrato de dados entre arquivos de configuracao.
- Detecta se a estrutura do projeto explicita camada de dados.
- Retorna metrica de contratos encontrados.

Regras implementadas:

- `data_contract_files`: arquivos em `context.config_files` cujo nome inicia com `schema` ou `contract`.
- Sem contratos: finding `MEDIUM`, categoria `DATA_QUALITY`.
- Sem qualquer parte de caminho contendo `data`: finding `LOW`, indicando que uma camada de validacao de dados nao esta obvia.

Metricas:

- `data_contract_files`

Referências:

- `src/dev_right_hand/agents/data_quality.py:7` define `DataQualityAgent`.
- `src/dev_right_hand/agents/data_quality.py:10` implementa `analyze`.
- `src/dev_right_hand/agents/data_quality.py:13` calcula `data_contract_files`.
- `src/dev_right_hand/agents/data_quality.py:17` cria finding para contratos ausentes.
- `src/dev_right_hand/agents/data_quality.py:29` cria finding para camada de dados nao obvia.
- `src/dev_right_hand/agents/data_quality.py:41` define metrica.

### `src/dev_right_hand/agents/ml_validation.py`

Agente de prontidao para validacao de ML.

Funcionalidade:

- Detecta arquivos relacionados a treinamento, features ou modelos.
- Verifica se codigo de treinamento possui testes.
- Verifica sinais de tracking de experimentos.
- Gera finding informativo quando nao ha modulos de treinamento explicitos.

Regras implementadas:

- `training_related`: arquivos Python cujo nome contém `train`, `fit`, `model` ou `feature`.
- Codigo de treinamento sem testes: finding `HIGH`, categoria `ML_VALIDATION`.
- Codigo de treinamento sem config relacionada a `mlflow`: finding `MEDIUM`.
- Nenhum arquivo de treinamento detectado: finding `INFO`.

Metricas:

- `training_related_files`
- `model_files`

Referências:

- `src/dev_right_hand/agents/ml_validation.py:7` define `MLValidationAgent`.
- `src/dev_right_hand/agents/ml_validation.py:10` implementa `analyze`.
- `src/dev_right_hand/agents/ml_validation.py:13` calcula `training_related`.
- `src/dev_right_hand/agents/ml_validation.py:20` detecta treinamento sem testes.
- `src/dev_right_hand/agents/ml_validation.py:32` detecta ausencia de tracking de experimentos.
- `src/dev_right_hand/agents/ml_validation.py:44` cria finding informativo quando nao ha treinamento.
- `src/dev_right_hand/agents/ml_validation.py:56` define metricas.
- `tests/test_orchestrator.py:21` garante presenca do agente no relatorio consolidado.

### `src/dev_right_hand/agents/llm_safety.py`

Agente de seguranca e governanca para fluxos LLM/agenticos.

Funcionalidade:

- Detecta arquivos relacionados a agentes, prompts, LLM ou RAG.
- Verifica se ha arquivos de configuracao/politica em YAML, YML ou JSON.
- Recomenda formalizacao de guardrails quando ha sinais de LLM.

Regras implementadas:

- `llm_related`: arquivos Python cujo nome contém `agent`, `prompt`, `llm` ou `rag`.
- LLM sem configs YAML/YML/JSON: finding `MEDIUM`.
- Qualquer presenca de LLM: finding `MEDIUM` recomendando suites de avaliacao para groundedness, prompt injection, drift e uso inseguro de ferramentas.

Metricas:

- `llm_related_files`

Referências:

- `src/dev_right_hand/agents/llm_safety.py:7` define `LLMSafetyAgent`.
- `src/dev_right_hand/agents/llm_safety.py:10` implementa `analyze`.
- `src/dev_right_hand/agents/llm_safety.py:13` calcula `llm_related`.
- `src/dev_right_hand/agents/llm_safety.py:20` detecta ausencia de configuracao de prompt/politica.
- `src/dev_right_hand/agents/llm_safety.py:32` recomenda formalizacao de guardrails.
- `src/dev_right_hand/agents/llm_safety.py:44` define metrica.

### `src/dev_right_hand/agents/observability.py`

Agente de observabilidade operacional.

Funcionalidade:

- Detecta arquivos relacionados a logs ou traces.
- Gera finding quando nao ha modulo obvio de observabilidade.
- Sempre recomenda definicao de estrategia de alertas.
- Retorna metrica de arquivos relacionados a observabilidade.

Regras implementadas:

- `log_related`: arquivos Python cujo nome contém `log` ou `trace`.
- Sem arquivos de log/trace: finding `MEDIUM`, categoria `OBSERVABILITY`.
- Estrategia de alertas: finding `LOW`, sempre emitido.

Metricas:

- `observability_related_files`

Referências:

- `src/dev_right_hand/agents/observability.py:7` define `ObservabilityAgent`.
- `src/dev_right_hand/agents/observability.py:10` implementa `analyze`.
- `src/dev_right_hand/agents/observability.py:13` calcula `log_related`.
- `src/dev_right_hand/agents/observability.py:17` cria finding para observabilidade ausente.
- `src/dev_right_hand/agents/observability.py:29` cria finding sobre estrategia de alertas.
- `src/dev_right_hand/agents/observability.py:40` define metrica.

## Testes

### `tests/test_agents.py`

Valida comportamento unitario do `CodeReviewAgent`.

Funcionalidade:

- Cria estrutura temporaria com um arquivo Python de aplicacao.
- Monta `RepositoryContext` sem testes e sem configs.
- Executa `CodeReviewAgent().run(context)`.
- Verifica que ha finding de categoria `CODE_QUALITY`.
- Verifica que existe finding com titulo `Tests are missing`.

Importancia técnica:

- Garante que a regra de ausencia de testes permanece ativa.
- Exercita o metodo publico `run`, nao apenas `analyze`, cobrindo tambem a montagem de `AgentReport`.

Referências:

- `tests/test_agents.py:7` define o teste.
- `src/dev_right_hand/agents/code_review.py:29` implementa a regra validada.

### `tests/test_orchestrator.py`

Valida montagem de contexto e execucao consolidada do orquestrador.

Funcionalidade:

- Cria diretorios temporarios `src` e `tests`.
- Cria `pyproject.toml`.
- Cria arquivo `train_model.py`.
- Cria arquivo `test_train_model.py`.
- Executa `MultiAgentOrchestrator.analyze()`.
- Verifica raiz do relatorio, quantidade de agentes, existencia de `run_id` e presenca do `MLValidationAgent`.

Importancia técnica:

- Confirma que o orquestrador executa os cinco agentes padrao.
- Confirma que arquivos de treinamento sao detectados dentro do fluxo consolidado.
- Valida integracao entre `AppConfig`, `MultiAgentOrchestrator`, agentes e contratos.

Referências:

- `tests/test_orchestrator.py:7` define o teste.
- `src/dev_right_hand/orchestrator.py:30` monta o contexto.
- `src/dev_right_hand/orchestrator.py:57` executa análise.

### `tests/test_tracking.py`

Valida o tracker de eventos.

Funcionalidade:

- Instancia `ExecutionTracker`.
- Registra evento `started` com detalhe `repository`.
- Registra evento `finished` com detalhe `findings`.
- Verifica que dois eventos foram armazenados.
- Verifica o nome do agente no primeiro evento.
- Verifica os detalhes do segundo evento.

Importancia técnica:

- Garante que `record()` cria eventos e preserva detalhes arbitrarios.
- Garante que a property `events` permite inspecionar o historico gerado.

Referências:

- `tests/test_tracking.py:4` define o teste.
- `src/dev_right_hand/tracking.py:26` implementa `record`.
- `src/dev_right_hand/tracking.py:23` implementa `events`.

## Relação entre contratos e agentes

Todos os agentes concretos seguem o mesmo padrao:

1. Recebem `RepositoryContext`.
2. Avaliam listas de arquivos ja preparadas pelo orquestrador.
3. Criam zero ou mais `Finding`.
4. Criam uma ou mais `AgentMetric`.
5. Retornam uma string `summary`.
6. Deixam `BaseAgent.run()` transformar esses dados em `AgentReport`.

Essa padronizacao reduz acoplamento entre agentes e orquestrador. O orquestrador nao precisa conhecer as regras internas de cada agente; ele apenas chama `run(context)` e coleta o relatorio.

Referências:

- `src/dev_right_hand/contracts.py:48` define `RepositoryContext`.
- `src/dev_right_hand/contracts.py:31` define `Finding`.
- `src/dev_right_hand/contracts.py:42` define `AgentMetric`.
- `src/dev_right_hand/contracts.py:57` define `AgentReport`.
- `src/dev_right_hand/agents/base.py:12` padroniza execucao.

## Pontos de atenção técnica

1. **Dois dominios no mesmo repositório**
   - O pacote `dev_right_hand` e o prototipo CrewAI médico coexistem, mas nao compartilham arquitetura.
   - Isso pode ser intencional para experimentacao, mas em producao convem separar ou integrar explicitamente.

2. **`agents.py` importa `FileReadTool` sem uso**
   - A importacao em `agents.py` nao afeta execucao, mas pode ser removida se nao houver plano de uso.

3. **`main.py` assume existencia de `logs/`**
   - A escrita em `logs/last_run_output.json` pode falhar se o diretorio nao existir.

4. **Heuristicas atuais sao estruturais**
   - Os agentes do pacote analisam nomes e presenca de arquivos, nao conteudo semantico profundo.
   - Isso e adequado para scaffold inicial, mas deve evoluir para análises reais com ferramentas como `ruff`, `pytest`, coverage, MLflow, OpenTelemetry e suites de avaliacao LLM.

5. **Execucao dos agentes e sequencial**
   - `MultiAgentOrchestrator.analyze()` executa agentes em loop simples.
   - Como os agentes atuais nao dependem entre si, ha oportunidade futura de paralelizacao.

6. **`ThresholdSettings` ainda nao e usado pelos agentes**
   - `config.py` define thresholds, mas as regras atuais usam valores fixos.
   - Uma evolucao natural e fazer agentes consultarem `config.thresholds`.

## Comandos relacionados

Instalação em modo desenvolvimento:

```bash
pip install -e .[dev]
```

Executar análise:

```bash
dev-right-hand scan .
```

Executar testes:

```bash
pytest
```

Executar prototipo médico:

```bash
python main.py
```
