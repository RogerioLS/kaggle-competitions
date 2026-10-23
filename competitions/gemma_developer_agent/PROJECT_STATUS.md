# 📋 Status Geral do Projeto e Guia de Retomada (Handoff)

> **Data de Atualização:** 23 de Outubro de 2026  
> **Repositório:** `RogerioLS/kaggle-competitions`  
> **Branch Atual:** `main` (100% atualizada e sincronizada com `origin/main`)  
> **Status de Qualidade:** 🟢 120/120 Testes Unitários Passando | Clean Chassis Compliant  

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
  4. **Ausência de Adaptadores LoRA:** O pacote submetido continha apenas a arquitetura base sem pesos de fine-tuning (`adapters/`) especializados nas tarefas de modificação cirúrgica de código.

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

### Fase 1: Blindagem de Prompts com Few-Shot Tool Calling
- **Diretiva Anti-Chat Mandatória:** Inserir nos prompts (`system.md`, `drafter.md`, `validator.md`) a regra rígida:
  > *"CRITICAL RULE: DO NOT CHAT. DO NOT EXPLAIN. DO NOT APOLOGIZE. Your output must strictly be a single valid JSON block containing the action and arguments."*
- **Injeção de Exemplos Few-Shot:** Adicionar 2 exemplos concretos de chamada de ferramenta por prompt:
  1. Chamada de leitura: `{"action": "read_file", "arguments": {"filepath": "...", "start_line": 1, "end_line": 30}}`
  2. Chamada de edição cirúrgica: `{"action": "edit_file", "arguments": {"filepath": "...", "old_string": "...", "new_string": "..."}}`
  3. Chamada de selamento obrigatória: `{"action": "submit_patch", "arguments": {}}`

### Fase 2: Calibração de Turn Budgets & Roteamento em `agent.yaml`
- Aumentar o budget de turnos do `drafter` de 5 para 8 turnos.
- Aumentar o budget do `validator` de 5 para 8 turnos.
- Configurar transição direta para o `drafter` se a localização do arquivo for confirmada no primeiro turno.

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
