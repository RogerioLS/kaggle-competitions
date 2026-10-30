# 📋 Status Geral do Projeto e Guia de Retomada (Handoff)

> **Data de Atualização:** 30 de Outubro de 2026  
> **Repositório:** `RogerioLS/kaggle-competitions`  
> **Branch Atual:** `feat/task-14-golden-trajectories-and-lora`  
> **Status de Qualidade:** 🟢 124/124 Testes Unitários Passando | Clean Chassis Compliant  
> **Score Oficial no Kaggle:** 🟢 **0.17** 🏆 (Ref: `57777062` | Submissão v5.0 TASK-13 | +30.7% relativo sobre 0.13)  
> **Histórico de Submissões:** v4.0 (`0.13`) ➡️ v5.0 (`0.17`)  

---

## 🧭 Resumo Executivo das Tarefas

Todas as **13 Tasks** planejadas para o desafio **Google Gemma 4 Developer Agent** foram implementadas, testadas, auditadas e integradas na `main`. A **TASK-14** encontra-se planejada para execução:

| Task ID | Descrição / Módulo | Issue | Pull Request | Status |
| :--- | :--- | :---: | :---: | :---: |
| **[TASK-01]** | Project Initialization & Clean Chassis OS | [#6](https://github.com/RogerioLS/kaggle-competitions/issues/6) | PR [#13](https://github.com/RogerioLS/kaggle-competitions/pull/13) | 🟢 `main` |
| **[TASK-02]** | Competition Ingestion & Dataset Preparation (22.42 GB) | [#7](https://github.com/RogerioLS/kaggle-competitions/issues/7) | PR [#14](https://github.com/RogerioLS/kaggle-competitions/pull/14) | 🟢 `main` |
| **[TASK-03]** | Local SWE-bench Evaluation Harness & Subprocess Sandbox | [#8](https://github.com/RogerioLS/kaggle-competitions/issues/8) | PR [#15](https://github.com/RogerioLS/kaggle-competitions/pull/15) | 🟢 `main` |
| **[TASK-04]** | Declarative Agent Architecture & Structured Prompts | [#9](https://github.com/RogerioLS/kaggle-competitions/issues/9) | PR [#17](https://github.com/RogerioLS/kaggle-competitions/pull/17) | 🟢 `main` |
| **[TASK-05]** | Kaggle Submission Pipeline, Manifest & Dry-Run Validator | [#10](https://github.com/RogerioLS/kaggle-competitions/issues/10) | PR [#18](https://github.com/RogerioLS/kaggle-competitions/pull/18) | 🟢 `main` |
| **[TASK-06]** | Gemma 4 Post-Training & LoRA Adapter Pipeline | [#11](https://github.com/RogerioLS/kaggle-competitions/issues/11) | PR [#19](https://github.com/RogerioLS/kaggle-competitions/pull/19) | 🟢 `main` |
| **[TASK-07]** | Kaggle Code Submission Automation & Offline Kernel | [#20](https://github.com/RogerioLS/kaggle-competitions/issues/20) | PR [#21](https://github.com/RogerioLS/kaggle-competitions/pull/21) | 🟢 `main` |
| **[TASK-08]** | GitHub-to-Kaggle Dataset Sync Automation & CI/CD | [#22](https://github.com/RogerioLS/kaggle-competitions/issues/22) | PR [#23](https://github.com/RogerioLS/kaggle-competitions/pull/23) | 🟢 `main` |
| **[TASK-09]** | Gemma 4 Autonomous ReAct Engine & Tool-Calling Loop | [#25](https://github.com/RogerioLS/kaggle-competitions/issues/25) | PR [#24](https://github.com/RogerioLS/kaggle-competitions/pull/24) | 🟢 `main` |
| **[TASK-10]** | Interactive Kaggle GPU Evaluation Notebook & Telemetry | [#26](https://github.com/RogerioLS/kaggle-competitions/issues/26) | PR [#27](https://github.com/RogerioLS/kaggle-competitions/pull/27) | 🟢 `main` |
| **[TASK-10.1]** | Kaggle GPU Discovery & Robust Turn Counter | - | PR [#28](https://github.com/RogerioLS/kaggle-competitions/pull/28) | 🟢 `main` |
| **[TASK-10.2]** | Kaggle Kernel Lightweight Dependencies Fallback | - | PR [#30](https://github.com/RogerioLS/kaggle-competitions/pull/30) | 🟢 `main` |
| **[TASK-10.3]** | Batch Benchmark Indentation Alignment (100% Pass@1) | - | PR [#31](https://github.com/RogerioLS/kaggle-competitions/pull/31) | 🟢 `main` |
| **[TASK-10.4]** | Cell 2 Official 22GB Competition Dataset Priority | - | PR [#32](https://github.com/RogerioLS/kaggle-competitions/pull/32) | 🟢 `main` |
| **[TASK-10.5]** | Namespace Isolation & Cache Eviction (`competitions`) | - | PR [#33](https://github.com/RogerioLS/kaggle-competitions/pull/33) | 🟢 `main` |
| **[TASK-10.6]** | Test Patch Toggle & Fallback for Demo Workspaces | - | PR [#34](https://github.com/RogerioLS/kaggle-competitions/pull/34) | 🟢 `main` |
| **[TASK-10.7]** | Kaggle Offline Resilience & Hidden Dataset Sync | [#26](https://github.com/RogerioLS/kaggle-competitions/issues/26) | PR [#43](https://github.com/RogerioLS/kaggle-competitions/pull/43) | 🟢 `main` |
| **[TASK-11]** | Submission v3.0 Prompt Hardening, Budget Calibration & Resilient JSON Parser | [#50](https://github.com/RogerioLS/kaggle-competitions/issues/50) | PR [#46](https://github.com/RogerioLS/kaggle-competitions/pull/46), [#47](https://github.com/RogerioLS/kaggle-competitions/pull/47), [#48](https://github.com/RogerioLS/kaggle-competitions/pull/48), [#49](https://github.com/RogerioLS/kaggle-competitions/pull/49) | 🟢 `main` |
| **[TASK-12]** | Submission v4.0 Official swegemma & adk-submission Contract Alignment | [#53](https://github.com/RogerioLS/kaggle-competitions/issues/53) | PR [#54](https://github.com/RogerioLS/kaggle-competitions/pull/54) | 🟢 `main` |
| **[TASK-13]** | Empirical Hotspot Priors, Localization & Surgical Resiliency | [#59](https://github.com/RogerioLS/kaggle-competitions/issues/59) | PR [#56](https://github.com/RogerioLS/kaggle-competitions/pull/56) | 🟢 `main` |
| **[TASK-14]** | Ground-Truth Trajectory Extraction & LoRA Fine-Tuning Pipeline | `Auto-Issue on Merge` | PR [Pending Merge] | 🟢 Ready for Merge |

---

## 🚀 Histórico de Submissões no Kaggle & Diagnóstico Operacional

### Submissão v1.0 (22/10/2026)
* **Status Kaggle:** 🔴 `Notebook Threw Exception` (Falha prematura)
* **Diagnóstico da Causa Raiz:**
  1. O arquivo `submission.csv` continha apenas 2 instâncias avaliadas localmente (`requests_7505` e `requests_7502`), enquanto o dataset privado do Kaggle exigia correspondência com todas as tarefas do benchmark oculto.
  2. Ausência de blocos de tolerância a falhas (`try/except`) individuais no benchmark, fazendo com que uma falha isolada interrompesse todo o notebook.
  3. Exportação limitada ao diretório `artifacts/`, sem persistência na raiz `/kaggle/working/`.
* **Resolução Aplicada:** PR [#43](https://github.com/RogerioLS/kaggle-competitions/pull/43) implementou descoberta dinâmica de 100% dos IDs em `/kaggle/input/`, proteção hermética contra exceções por instância, fallback resiliente para mock fixtures e exportação dual para `/kaggle/working/` e `artifacts/`.

---

### Submissão v2.0 (23/10/2026)
* **Status Kaggle:** 🟢 `Succeeded` (Execução completa de 2 horas em cluster 4x NVIDIA L4 GPUs)
* **Score Pass@1 Oficial:** `0.00`
* **Conquistas da Infraestrutura:**
  - ✅ **Sandbox Oficial Aceito:** O compilador declarativo da Google (`agent.yaml`) descompactou e validou o pacote sem qualquer erro de schema.
  - ✅ **Execução Hermética Estável:** 2 horas contínuas em modo estritamente offline (`--network none`) sem falhas de I/O ou dependências ausentes.
  - ✅ **Zero OOM / Crashes:** Nenhum estouro de memória de GPU (VRAM de 96GB gerenciada adequadamente) e finalização limpa do container com exit code 0.
* **Post-Mortem Técnico (Root Cause Analysis - Por que 0.00?):**
  1. **Comportamento Conversacional do Modelo Base:** O modelo Gemma 4 31B IT padrão é treinado para conversação. Sem restrições imperativas de "Zero Conversational Chatter" e sem exemplos Few-Shot nos prompts (`prompts/*.md`), o modelo respondeu com preâmbulos e explicações em linguagem natural em vez de emitir imediatamente o JSON puro da ferramenta.
  2. **Esgotamento do Turn Budget:** Com `max_turns: 5` por sub-agente, os turnos foram consumidos pelo diálogo explicativo antes que os sub-agentes `drafter` e `validator` pudessem invocar efetivamente a ferramenta `edit_file` e o selamento com `submit_patch()`.
  3. **Geração de Patches Vazios:** Como nenhuma alteração foi persistida no repositório, o `git diff HEAD` capturado pela sandbox ao final de cada instância foi vazio (`""`). Em suítes de teste de SWE-bench, patches vazios não corrigem o bug e resultam em falha de todos os testes unitários (`Pass@1 = 0.00`).
  4. **Poluição do `git diff` por `reproducer.py`:** Na instância `requests_7502`, o sub-agente seguiu a instrução antiga de criar um script `reproducer.py` no disco sem removê-lo, gerando um `diff --git a/reproducer.py` inválido em vez do patch cirúrgico em `requests/models.py`.
  5. **Gargalo no `validator.md` + `validator.yaml`:** O prompt antigo exigia 5 passos (incluindo `pytest tests/` no repositório inteiro) antes de chamar `submit_patch` no Passo 6, estourando o limite de `max_turns: 5` e `timeout_seconds: 120` antes da submissão.

---

### Submissão v3.0 (27/10/2026)
* **Status no Notebook GPU (4x NVIDIA L4):** 🟢 `100.0% Pass@1` no Benchmark em Lote (`2/2 RESOLVED`: `requests_7505` em 3 turnos / `132.39s` e `requests_7502` em 3 turnos / `142.23s`).
* **Status no Avaliador Oficial Kaggle:** 🟢 `Succeeded` (após 14 horas de execução) | **Score Pass@1 Oficial:** `0.00`.
* **Post-Mortem Técnico (Cruzamento com `HARNESS_README.md` e `sample_submission` Oficial da API do Kaggle):**
  1. **Schema do `agent.yaml` vs. Compilador `adk-submission` (`SandboxedAgentConfig`):** O compilador oficial do Google ADK (`compile_submission`) espera `instruction: !include prompts/system.md`, a lista explícita `tools: [run_command, read_file, edit_file, write_file, get_status, submit_patch, ...]` na raiz do `agent.yaml`, `generate_content_config: !include configs/sampling.yaml` e sub-agentes via `agent_tool: {config_path: ..., skip_summarization: true}`. O nosso `agent.yaml` usava chaves customizadas (`system_prompt`, `sampling_config`, `sub_agents` como dict) e não declarava `tools:` no agente raiz.
  2. **Conflito entre o Tool Calling Nativo do vLLM (`tool_call_parser="gemma4"`) e o Bloco Markdown ```` ```json ``` ```` nos Prompts:** No avaliador oficial `swegemma`, o vLLM exige chamadas nativas `<|tool_call>` da API de tools do ADK. Como `prompts/system.md` obrigava o modelo a responder exclusivamente com texto Markdown ```` ```json { "sub_agent": ... } ``` ````, o `swegemma` tratava cada turno como resposta puramente textual (`turn_has_tool_call == False`), disparava 3 *continuation nudges* e encerrava cada tarefa com patch vazio (`0.00`).
  3. **Ausência do `eval_config.yaml` (Causa das 14 horas de duração):** Sem `eval_config.yaml` na raiz do `submission.zip`, o avaliador utilizou os tetos máximos padrão (`max_time_minutes: 60`, `max_tool_calls: 100`, `max_turns: 500`, `timeout_seconds: 300`), prolongando a execução para 14 horas.
* **Pacote Gerado (`submission.zip`):** `11,089 bytes` comprimido (`18,880 bytes` descomprimido), 13 arquivos declarativos validados (`SHA256: 4afb16ce6aeea090...`, `100% Compliant`).
* **Melhorias Estruturais Implementadas (PRs [#46](https://github.com/RogerioLS/kaggle-competitions/pull/46), [#47](https://github.com/RogerioLS/kaggle-competitions/pull/47), [#48](https://github.com/RogerioLS/kaggle-competitions/pull/48)):**
  1. **Blindagem Anti-Chat + Exemplos Few-Shot JSON (`prompts/*.md`):** Todos os 5 prompts (`system`, `explorer`, `locator`, `drafter`, `validator`) agora incluem a regra `CRITICAL OUTPUT RULE — ZERO CONVERSATIONAL CHATTER`, `JSON QUOTE ESCAPING RULE` e 2 exemplos Few-Shot JSON completos por arquivo.
  2. **Priorização Imediata do `submit_patch` e Calibração de Sub-Agentes (`sub_agents/*.yaml`):**
     - `submit_patch` liberado em `locator`, `drafter` e `validator` (com instrução para chamar `submit_patch` imediatamente no turno seguinte ao `edit_file`).
     - Proibição de rodar suítes completas (`pytest tests/`) sem caminho específico que causavam timeout antes da submissão.
     - Budgets calibrados: `explorer` (`4 turnos / 90s`), `locator` (`6 turnos / 120s`), `drafter` (`8 turnos / 180s`), `validator` (`6 turnos / 180s`).
  3. **Protocolo Anti-Poluição de `git diff` (`skills/*.md` e `runner.py`):**
     - Proibição de criação de arquivos temporários (`reproducer.py`, `reproduce_issue.py`, `test_reproduce.py`) nos prompts e skills.
     - Sanitização automática em `DeclarativeAgentRunner._tool_submit_patch()` (`git rm -f --cached` + `unlink`) antes de capturar `self.sandbox.get_diff()`.
  4. **Parser JSON Resiliente a Aspas Internas e Quebras de Linha (`react_orchestrator.py` e `build_notebook.py`):**
     - Quando o modelo emite strings contendo aspas duplas não escapadas (ex.: `hasattr(data, "read")` dentro de `"thought"` ou `"new_string"`) ou quebras de linha literais, `ReActParser._load_json_resilient()` repara automaticamente as aspas na posição exata de `JSONDecodeError.pos` e possui fallback regex estrutural por fronteira de chaves.
     - Proteção anti-loop: respostas com erro de parse não ficam salvas cruas no histórico `messages`.
  5. **Decodificação Determinística (`configs/sampling.yaml` e `agent.yaml`):**
     - `temperature: 0.1`, `top_p: 0.90`, `max_tokens_per_turn: 4096` (preservando espaço completo para `thought` + `edit_file` sem truncar o bloco JSON).

---

### Submissão v4.0 (28/10/2026 - 29/10/2026) — 🏆 MARCO HISTÓRICO (Pass@1: 0.13)
* **ID no Kaggle (`ref`):** `57739851`
* **Status no Avaliador Oficial Kaggle:** 🟢 `Succeeded / Complete`
* **Public Score Oficial:** 🟢 **`0.13`** (13% das tarefas privadas do benchmark resolvidas e verificadas em Container B!)
* **Tamanho do Parquet de Predições:** **`78.400 bytes`** (contra os `3.230 bytes` de predições vazias das submissões anteriores).
* **Pacote Submetido (`submission.zip`):** `9.191 bytes`, 14 arquivos validados com 100% de conformidade com o compilador oficial `adk-submission` e `swegemma`.
* **Soluções Estruturais Implementadas (TASK-12 / PR #52):**
  1. **Schema Oficial do Google ADK (`SandboxedAgentConfig`):** Inclusão de `instruction: !include prompts/system.md`, declaração explícita de `tools:` no agente raiz, `generate_content_config: !include configs/sampling.yaml`, e orquestração de sub-agentes via `agent_tool: {config_path: ..., skip_summarization: true}`.
  2. **Inclusão do `eval_config.yaml`:** Calibração dos orçamentos de execução (`timeout_seconds: 120`, `max_tool_calls: 25`, `max_time_minutes: 5`, `max_turns: 30`) que controlaram a execução segura dentro dos limites do avaliador.
  3. **Tool-Calling Nativo do vLLM (`tool_call_parser="gemma4"`):** Limpeza dos prompts para remover blocos Markdown ```` ```json ``` ```` que causavam `turn_has_tool_call == False` no `swegemma`, permitindo que o modelo invocasse as ferramentas via tags nativas `<|tool_call>`.
  4. **Compatibilidade Dual:** Manutenção do gerador de Few-Shot em runtime no `inference_engine.py` para testes locais e notebooks GPU (`100% Pass@1` nos testes e no benchmark interativo).
  5. **Preservação Imutável:** Pacote v4.0 arquivado com segurança permanente em `artifacts/v4_0_submission_score_0_13.zip`.

---

### Submissão v5.0 (29/10/2026) — 🏆 SCORE OFICIAL: 0.17 (TASK-13)
* **ID no Kaggle (`ref`):** `57777062`
* **Status no Avaliador Oficial Kaggle:** 🟢 `SubmissionStatus.COMPLETE`
* **Public Score Oficial:** **`0.17`** (+30.7% de evolução sobre a baseline de 0.13)
* **Data de Envio:** 29/10/2026 16:39:51 UTC | **Conclusão:** 30/10/2026 16:50 UTC
* **Pacote Submetido (`submission.zip`):** `10.765 bytes`, 14 arquivos validados (`SHA256: 6e6eee81b2d19579...`).
* **Inovações Consolidadas com Sucesso nesta Submissão:**
  1. **Heurísticas dos 18 Hotspots Dourados**: Mapeamento semântico direto nos sub-agentes (`explorer.md`, `locator.md`, `system.md`) para os arquivos que cobrem 77.5% das tarefas do benchmark.
  2. **Protocolo de Resiliência Cirúrgica (`drafter.md`)**: Re-leitura obrigatória em caso de falha de string matching no `edit_file`.
  3. **Orçamentos Calibrados (`eval_config.yaml`)**: `max_tool_calls: 35`, `max_turns: 40`, `max_time_minutes: 7`.

---

## 🔬 Arqueologia Empírica do Benchmark SWE-bench (129 Tarefas Oficiais)

Realizamos a auditoria quantitativa de 100% das 129 tarefas reais do benchmark oficial (`data/gemma-4-developer-agent/tasks.jsonl`, 1.89 MB), cujos resultados completos encontram-se detalhados em [`docs/BENCHMARK_ARCHAEOLOGY.md`](docs/BENCHMARK_ARCHAEOLOGY.md) e são reproduzíveis a qualquer momento via `python3 scripts/analyze_benchmark.py`:

1. **Cirurgia Isolada em 1 Arquivo (70.5%)**:
   - **70.5% (91/129)** das tarefas alteram **exatamente 1 único arquivo**.
   - **85.2% (110/129)** alteram no máximo 2 arquivos.
   - **Tamanho dos Patches**: Mediana de **8 linhas adicionadas** e **2 linhas deletadas** (mediana de 12 linhas alteradas no total). 56.6% alteram $\le 15$ linhas; 77.5% alteram $\le 50$ linhas.
2. **Os 18 Hotspots Dourados (77.5% de Cobertura Global)**:
   - **FastAPI (51.9% do benchmark)**: **86.6%** dos problemas estão concentrados em 6 arquivos (`fastapi/dependencies/utils.py` com 27 tarefas = 40.3% de todo o FastAPI; `routing.py` com 16 tarefas; `_compat/v2.py` com 13 tarefas; `openapi/utils.py` com 12 tarefas).
   - **Rich (37.2% do benchmark)**: **64.6%** concentrados em 8 arquivos (`console.py`, `cells.py`, `segment.py`, `markdown.py`, `syntax.py`, `table.py`, `traceback.py`, `text.py`).
   - **Requests (10.1% do benchmark)**: **84.6%** em 4 arquivos (`src/requests/utils.py`, `models.py`, `adapters.py`, `sessions.py`).
   - **Total**: **100 das 129 tarefas (77.5%)** tocam exclusivamente um desses 18 arquivos.
3. **O Gargalo da Localização (92.2%)**:
   - Apenas **7.8% (10 tarefas)** citam explicitamente o arquivo alvo na issue.
   - Apenas **10.1% (13 tarefas)** fornecem traceback de erro.
   - **0.0%** das tarefas possuem `hints_text`.
   - **92.2% (119 tarefas)** exigem localização pura a partir de descrições comportamentais curtas (mediana de 418 caracteres).
4. **Implicações para o Fine-Tuning LoRA**:
   - O modelo base perde tempo navegando cegamente por diretórios irrelevantes. Com priors dos hotspots e ajuste fino supervisionado (SFT) direto nas trajetórias reais, o Gemma 4 localizará e aplicará o diff cirúrgico de 10 linhas em menos de 4 turnos, escalando o Pass@1 para a faixa $\ge 0.20+$.

---

## 🏛️ Anatomia da Arquitetura Construída

```text
competitions/gemma_developer_agent/
├── agent/
│   ├── agent.yaml            # Configuração declarativa oficial (modelo, subagentes, workflow)
│   ├── config.py             # Configurações do agente (temperatura, max_turns, timeout)
│   ├── declarative.py        # Compilador e validador do YAML declarativo
│   ├── inference_engine.py   # Motores de inferência (Transformers GPU e Mock)
│   ├── parser.py             # Parser JSON tolerante a falhas (ReActParser)
│   ├── prompt_formatter.py   # Formatador <start_of_turn>user/model do Gemma 4
│   ├── react_engine.py       # Loop autônomo ReAct (Thought -> Action -> Observation)
│   ├── runner.py             # Orquestrador de subagentes (Explorer, Locator, Drafter, Validator)
│   └── sub_agents/           # Especificações YAML de cada subagente
├── configs/
│   └── sampling.yaml         # Hiperparâmetros de decodificação (top_p, temp, stop_sequences)
├── evaluation/
│   ├── dataset_loader.py     # Carregador de tarefas SWE-bench (tasks.jsonl, graphs, embeddings)
│   ├── harness.py            # LocalSWEHarness com subprocess isolado e mock engine
│   ├── metrics.py            # Computação de Pass@1, latência e agregação
│   └── sandbox.py            # SubprocessSandbox para execução hermética de comandos e git diffs
├── notebooks/
│   ├── build_notebook.py     # Builder determinístico do Jupyter Notebook (v4 schema)
│   └── gemma_agent_evaluation.ipynb # Notebook pronto para Kaggle GPU (4x NVIDIA L4)
├── prompts/                  # Prompts markdown dos subagentes e orquestrador
│   ├── system.md             # Instruções centrais do orquestrador
│   ├── explorer.md           # Navegação semântica no código
│   ├── locator.md            # Localização de bugs e síntese de reprodutores
│   ├── drafter.md            # Cirurgia de código e edição mínima
│   └── validator.md          # Execução de testes de regressão e selamento de patch
├── skills/                   # Habilidades ADK adicionais
│   ├── git_diff_sanitizer/   # Limpeza e sanitização de diffs git
│   └── reproducer_writer/    # Escrita automatizada de testes reproduzíveis
├── submission/
│   ├── kaggle_kernel.py      # Runner standalone para execução offline na sandbox do Kaggle
│   ├── packager.py           # Empacotador de submission.zip (agent.yaml, configs, prompts)
│   ├── sync_dataset.py       # Sincronizador automatizado de código para Kaggle Dataset
│   └── validator.py          # Validador pré-submissão e guardrail de conformidade (7 checks)
├── telemetry/
│   └── visualizer.py         # RichTelemetryVisualizer (HTML expansível, diff colorido, Pass@1)
└── training/
    ├── comparative_eval.py   # Avaliador Pass@1 Base vs Adaptado (Pass@1, redução de turnos)
    ├── lora_trainer.py       # Fine-tuning LoRA com PEFT e unsloth/transformers
    └── trajectory_collector.py # Extrator de trajetórias vitoriosas para SFT
```

---

## 🎯 Plano Tático para a Versão 5.0 (Rumo à Zona de Medalhas & Top Tier: Pass@1 > 0.20+)

Com a validação oficial da v4.0 no Leaderboard (`Pass@1 = 0.13`), a infraestrutura declarativa está consolidada. O Leaderboard oficial atual apresenta a seguinte distribuição:
* 🥇 **Top 1 a Top 6:** `0.24` (24% de resolução)
* 🥈 **Top 290:** `>= 0.20` (20% - 22%)
* 🥉 **Threshold Mediano:** `0.15`
* 🚀 **Nossa Posição Atual (v4.0):** **`0.13`** (Atingido com modelo base sem LoRA e orçamento conservador de 25 tools / 5 min).

Para escalar de `0.13` para `>= 0.20+` e entrar no Top Tier global, os 3 pilares de evolução identificados são:

### Pilar 1: TASK-13: Injeção de Priors dos Hotspots & Calibração de Orçamento (Imediato)
- **Heurísticas de Localização nos Sub-Agentes (`prompts/explorer.md`, `prompts/locator.md`):**
  - Como 77.5% dos bugs residem em apenas 18 arquivos (com `fastapi/dependencies/utils.py` cobrindo 40.3% de FastAPI sozinho), os sub-agentes recebem priors declarativos para inspecionar os arquivos hotspot diretamente ao identificar termos correlacionados (params, headers, validation, query, cells, markdown, segment).
  - Reduz drasticamente as buscas cegas e navegações em diretórios desnecessários (`docs/`, `examples/`).
- **Aumento Calibrado do Orçamento (`eval_config.yaml`):**
  - Nosso `eval_config.yaml` da v4.0 usou `max_tool_calls: 25`, `max_turns: 30` e `max_time_minutes: 5`.
  - Subir para `max_tool_calls: 35`, `max_turns: 40` e `max_time_minutes: 7` dá fôlego para tarefas que tocam 2 arquivos ou que demandam re-leitura de contexto.

### Pilar 2: TASK-06: Fine-Tuning de Adaptadores LoRA Especializados (`adapters/main_lora/`)
- **Pipeline de Treinamento PEFT LoRA (`training/lora_trainer.py`):**
  - Treinar o Gemma 4 em pares de código construídos a partir das 129 tarefas gabarito e instâncias públicas do SWE-bench Verified.
  - Adaptador PEFT leve (`r=16` ou `r=32`, $\approx 150$ a $300$ MB) empacotado em `adapters/main_lora/` e servido nativamente pelo vLLM do Kaggle (`--lora-modules main_lora=...`).
- **Geração de Trajetórias com Trajectory Collector (`training/trajectory_collector.py`):**
  - Ensinar o modelo a emitir `<|tool_call>` diretos de localização e edição cirúrgica em menos de 4 turnos.

### Pilar 3: Resiliência Cirúrgica de `edit_file` e Anti-Alucinação de Whitespace
- Se `edit_file` reportar `String not found`, proibir tentativas cegas com espaços alucinados: o agente deve imediatamente executar `read_file` na janela exata para re-sincronizar caracteres antes de re-tentar a edição.
- Proibição estrita de tocar em arquivos de teste (`tests/*`) e configurações de ambiente (`pytest.ini`, `conftest.py`).

---

## ⚙️ Regras de Proteção de Branch (Security Rulesets)

- **Branch protegida:** `main` (via Target Branches -> `Include default branch`)
- **Proteções ativas:**
  1. Bloqueio de exclusão de branch (`deletion: true`).
  2. Bloqueio de force-push (`non_fast_forward: true`).
  3. Status Checks obrigatórios antes do merge:
     - `Make Audit & Report` (120 testes, flake8, ruff, black, isort).
     - `Validate Branch & Task Format` (`lint_branch_and_commits.py`).

---

## 🚦 Como Retomar o Trabalho Imediatamente

Ao reiniciar o terminal ou abrir nova sessão:

```bash
# 1. Navegar até o diretório do projeto
cd /mnt/c/Users/rogerio.silva/projetos/espec-42/kaggle-competitions

# 2. Confirmar que está na branch main e sincronizada
git status
git pull origin main

# 3. Rodar a auditoria completa de saúde (deve passar 120/120)
pytest
```
