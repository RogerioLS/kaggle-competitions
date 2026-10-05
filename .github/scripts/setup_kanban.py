#!/usr/bin/env python3
"""Idempotent GitHub Kanban & Issue Setup Automation.

Configures:
1. Milestones on GitHub
2. Labels on GitHub
3. Tasks/Issues on GitHub linked to milestones and labels

Authentication priority:
1. GITHUB_TOKEN or GH_TOKEN environment variable
2. ~/.github_token file
3. gh CLI auth token
"""

import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional

REPO = "RogerioLS/kaggle-competitions"
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ISSUES_DIR = BASE_DIR / ".github" / "issues"


def get_token() -> str:
    """Retrieves GitHub token from env or token file."""
    for var in ("GITHUB_TOKEN", "GH_TOKEN"):
        token = os.environ.get(var, "").strip()
        if token:
            return token

    token_file = Path.home() / ".github_token"
    if token_file.exists():
        token = token_file.read_text(encoding="utf-8").strip()
        if token:
            return token

    print("❌ Error: No GitHub token found in env or ~/.github_token.")
    sys.exit(1)


def api_request(
    url: str, method: str = "GET", data: Optional[Dict[str, Any]] = None, token: str = ""
) -> Any:
    """Executes a request to GitHub REST API with unverified SSL handling."""
    ctx = ssl._create_unverified_context()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "Kaggle-Competitions-Kanban-Setup",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    encoded_data = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, context=ctx) as resp:
            content = resp.read().decode("utf-8")
            return json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        if e.code == 422:  # Already exists or validation error
            try:
                return json.loads(body)
            except Exception:
                pass
        print(f"⚠️ API Error ({e.code}) on {method} {url}: {body}")
        return None
    except Exception as e:
        print(f"⚠️ Request Failed on {method} {url}: {e}")
        return None


def setup_milestones(token: str) -> Dict[str, int]:
    """Creates milestones idempotently and returns a map of title to milestone number."""
    print("🎯 Setting up Milestones...")
    url = f"https://api.github.com/repos/{REPO}/milestones"
    existing = api_request(f"{url}?state=all", token=token) or []
    milestone_map = {m["title"]: m["number"] for m in existing if "title" in m}

    milestones_def = [
        (
            "01. Ingestion & Local Benchmark Harness",
            "Competition kit, fixtures, dataset loader and local SWE-bench harness.",
        ),
        (
            "02. Declarative ADK Agent & Prompt Architecture",
            "Declarative agent.yaml, sub-agents (explorer, locator, drafter) & prompts.",
        ),
        (
            "03. Test-Driven Closed Loop & Code-Graphs",
            "Pytest closed-loop feedback, test reproducers, AST graphs & embeddings.",
        ),
        (
            "04. Kaggle Submission Pipeline, LoRA Training & Paper Track",
            "Submission.zip builder, Gemma 4 LoRA fine-tuning, and NeurIPS paper.",
        ),
    ]

    for title, desc in milestones_def:
        if title in milestone_map:
            print(f"  ✔ Milestone already exists (#{milestone_map[title]}): {title}")
        else:
            payload = {"title": title, "description": desc, "state": "open"}
            res = api_request(url, method="POST", data=payload, token=token)
            if res and "number" in res:
                milestone_map[title] = res["number"]
                print(f"  ➕ Created Milestone (#{res['number']}): {title}")

    return milestone_map


def setup_labels(token: str) -> None:
    """Creates labels idempotently."""
    print("🏷️ Setting up Labels...")
    url = f"https://api.github.com/repos/{REPO}/labels"
    existing = api_request(f"{url}?per_page=100", token=token) or []
    existing_names = {lbl["name"] for lbl in existing if "name" in lbl}

    labels_def = [
        ("area: competition", "20BEFF", "Competição e regras de submissão"),
        ("area: harness", "1abc9c", "Harness local de avaliação e sandbox SWE-bench"),
        ("area: agent", "9b59b6", "Arquitetura declarativa de agentes ADK"),
        ("area: lora", "e67e22", "Post-training e adaptadores LoRA"),
        ("area: submission", "f1c40f", "Empacotamento e validação de submission.zip"),
        ("area: paper", "34495e", "Paper Track e documentação científica NeurIPS"),
        ("type: feature", "27ae60", "Nova capacidade ou funcionalidade"),
        ("type: bugfix", "e74c3c", "Correção de defeito"),
        ("type: benchmark", "d35400", "Resultados de medição e scores"),
        ("type: docs", "7f8c8d", "Documentação e guias"),
        ("priority: high", "b91c1c", "Prioridade Alta / Bloqueante"),
        ("priority: medium", "f59e0b", "Prioridade Média"),
        ("priority: low", "10b981", "Prioridade Baixa"),
    ]

    for name, color, desc in labels_def:
        if name in existing_names:
            print(f"  ✔ Label already exists: {name}")
        else:
            payload = {"name": name, "color": color, "description": desc}
            res = api_request(url, method="POST", data=payload, token=token)
            if res:
                print(f"  ➕ Created Label: {name}")


def setup_tasks(token: str, milestone_map: Dict[str, int]) -> None:
    """Creates or updates issues on GitHub from .github/issues/*.md."""
    print("📋 Setting up Tasks & Issues on GitHub...")
    url = f"https://api.github.com/repos/{REPO}/issues"
    existing_issues = api_request(f"{url}?state=all&per_page=100", token=token) or []

    # Map title prefix / ID to existing issue number
    existing_map = {}
    for issue in existing_issues:
        title = issue.get("title", "")
        match = re.search(r"\[(TASK-\d+)\]", title)
        if match:
            existing_map[match.group(1)] = issue["number"]

    task_definitions = [
        {
            "id": "TASK-01",
            "title": "[TASK-01] Project Initialization and Architecture Scaffolding",
            "file": "task-01-scaffold.md",
            "milestone": "01. Ingestion & Local Benchmark Harness",
            "labels": ["area: competition", "type: feature", "priority: high"],
        },
        {
            "id": "TASK-02",
            "title": "[TASK-02] Gemma 4 Competition Ingestion & Dataset Preparation",
            "file": "task-02-competition-spec-and-dataset.md",
            "milestone": "01. Ingestion & Local Benchmark Harness",
            "labels": ["area: competition", "type: feature", "priority: high"],
        },
        {
            "id": "TASK-03",
            "title": "[TASK-03] Local SWE-bench Evaluation Harness & Benchmark Sandbox",
            "file": "task-03-local-swebench-harness.md",
            "milestone": "01. Ingestion & Local Benchmark Harness",
            "labels": ["area: harness", "type: feature", "priority: high"],
        },
        {
            "id": "TASK-04",
            "title": "[TASK-04] Declarative Agent Architecture & Structured Prompts",
            "file": "task-04-declarative-agent-baseline.md",
            "milestone": "02. Declarative ADK Agent & Prompt Architecture",
            "labels": ["area: agent", "type: feature", "priority: high"],
        },
        {
            "id": "TASK-05",
            "title": "[TASK-05] Kaggle Submission Pipeline, Validator & Dry-Run",
            "file": "task-05-submission-pipeline-and-dryrun.md",
            "milestone": "03. Test-Driven Closed Loop & Code-Graphs",
            "labels": ["area: submission", "type: feature", "priority: high"],
        },
        {
            "id": "TASK-06",
            "title": "[TASK-06] Gemma 4 Post-Training & LoRA Adapter Pipeline",
            "file": "task-06-lora-posttraining-pipeline.md",
            "milestone": "04. Kaggle Submission Pipeline, LoRA Training & Paper Track",
            "labels": ["area: lora", "type: feature", "priority: medium"],
        },
    ]

    for task in task_definitions:
        task_id = task["id"]
        title = task["title"]
        ms_title = task["milestone"]
        ms_number = milestone_map.get(ms_title)
        labels = task["labels"]
        file_path = ISSUES_DIR / task["file"]
        body = file_path.read_text(encoding="utf-8") if file_path.exists() else f"# {title}\n"

        if task_id in existing_map:
            iss_num = existing_map[task_id]
            print(f"  🔄 Updating existing Issue #{iss_num}: {title}")
            edit_url = f"https://api.github.com/repos/{REPO}/issues/{iss_num}"
            payload = {
                "title": title,
                "body": body,
                "milestone": ms_number,
                "labels": labels,
            }
            api_request(edit_url, method="PATCH", data=payload, token=token)
        else:
            print(f"  ➕ Creating new Issue: {title}")
            payload = {
                "title": title,
                "body": body,
                "milestone": ms_number,
                "labels": labels,
            }
            res = api_request(url, method="POST", data=payload, token=token)
            if res and "number" in res:
                print(f"     -> Created Issue #{res['number']} successfully!")


def main() -> None:
    print("==================================================")
    print(" 🚀 KAGGLE COMPETITIONS — GITHUB KANBAN SETUP     ")
    print("==================================================")
    token = get_token()
    milestone_map = setup_milestones(token)
    setup_labels(token)
    setup_tasks(token, milestone_map)
    print("==================================================")
    print(" ✅ SETUP DO KANBAN E ISSUES FINALIZADO COM SUCESSO! ")
    print("==================================================")


if __name__ == "__main__":
    main()
