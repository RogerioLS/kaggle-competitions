# 📋 Status Geral do Projeto e Guia de Retomada (Handoff)

> **Data de Atualização:** 27 de Outubro de 2026  
> **Repositório:** `RogerioLS/kaggle-competitions`  
> **Branch Atual:** `main` (100% atualizada e sincronizada com `origin/main`)  
> **Status de Qualidade:** 🟢 123/123 Testes Unitários Passando | Clean Chassis Compliant  

---

## 🧭 Resumo Executivo das Tarefas

Todas as **10 Tasks** planejadas para o desafio **Google Gemma 4 Developer Agent** foram implementadas, testadas, auditadas e integradas diretamente na branch `main`:

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
| **[TASK-10.8]** | Prompt Hardening, Budget Calibration, Diff Sanitizer & Resilient JSON Parser | [#9](https://github.com/RogerioLS/kaggle-competitions/issues/9) | PR [#46](https://github.com/RogerioLS/kaggle-competitions/pull/46), [#47](https://github.com/RogerioLS/kaggle-competitions/pull/47), [#48](https://github.com/RogerioLS/kaggle-competitions/pull/48) | 🟢 `main` |

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

### Submissão v3.0 (27/10/2026) — Em Avaliação no Kaggle
* **Status no Notebook GPU (4x NVIDIA L4):** 🟢 `100.0% Pass@1` no Benchmark em Lote (`2/2 RESOLVED`: `requests_7505` em 3 turnos / `132.39s` e `requests_7502` em 3 turnos / `142.23s`).
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

## 🎯 Plano Tático para a Versão 3.0 (Rumo à Zona de Medalhas: Pass@1 > 0.15)

O Leaderboard atual possui a seguinte distribuição de competidores:
* 🥇 **Top 1 (Ouro):** ~0.24 (24% de resolução)
* 🥈 **Top 2 a Top 6 (Prata/Bronze):** 0.17 a 0.18 (17% - 18%)
* 🥉 **Baselines Simples:** 0.10 a 0.12 (10% - 12%)

Para cruzar a barreira do zero e disputar a zona de medalhas, o plano de ataque está estruturado em 3 fases complementares:

### Fase 1: Blindagem de Prompts com Few-Shot Tool Calling — ✅ Concluída (PRs #46, #47, #48)
- **Diretiva Anti-Chat Mandatória:** Inserida nos 5 prompts (`system.md`, `explorer.md`, `locator.md`, `drafter.md`, `validator.md`) e nas 2 skills (`reproducer_writer`, `git_diff_sanitizer`).
- **Regra de Escapamento de Aspas (`JSON QUOTE ESCAPING RULE`) + Parser Resiliente:** Reparo automático de aspas duplas internas não escapadas (`hasattr(data, "read")`) e quebras de linha literais em `ReActParser`.
- **Injeção de Exemplos Few-Shot:** 2 exemplos concretos de chamada de ferramenta em formato JSON válido por prompt (`read_file`, `edit_file`, `submit_patch`).

### Fase 2: Calibração de Turn Budgets, Permissões & Sanitização — ✅ Concluída (PRs #47, #48)
- `drafter` calibrado para `8 turnos / 180s` e `validator` para `6 turnos / 180s`.
- Permissão de `submit_patch` liberada diretamente em `locator`, `drafter` e `validator`.
- Sanitização automática de scripts temporários (`reproducer.py`) em `_tool_submit_patch()` antes do `git diff`.
- Redução comprovada na GPU do Kaggle de **7 turnos (415s)** na v2.0 para **3 turnos (132s)** na v3.0 com **100% Pass@1** nas duas instâncias `requests_7505` e `requests_7502`.

### Fase 3: Post-Training com LoRA Adaptadores (Task 06)
- Coletar trajetórias reais de resolução com `training/trajectory_collector.py`.
- Treinar adaptadores PEFT LoRA em 4-bit (`training/lora_trainer.py`).
- Incluir a pasta `adapters/gemma4-swe-w4a16/` diretamente no `submission.zip` para garantir que o modelo pense nativamente em sintaxe de patch.

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
