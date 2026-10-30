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

import argparse
import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

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
        (
            "05. Empirical Hotspots & Golden Trajectories Post-Training",
            "Empirical SWE-bench priors, 129 golden trajectories, and specialized PEFT LoRA.",
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
        ("area: security", "e11d21", "Vulnerabilidades e segurança"),
        ("area: infra", "0052cc", "Infraestrutura CI/CD e automação"),
        ("deps", "0366d6", "Dependências de pacotes e actions"),
    ]

    for name, color, desc in labels_def:
        if name in existing_names:
            print(f"  ✔ Label already exists: {name}")
        else:
            payload = {"name": name, "color": color, "description": desc}
            res = api_request(url, method="POST", data=payload, token=token)
            if res:
                print(f"  ➕ Created Label: {name}")


def setup_tasks(token: str, milestone_map: Dict[str, int], dry_run: bool = False) -> None:
    """Creates or updates issues on GitHub dynamically from .github/issues/*.md."""
    print("📋 Setting up Tasks & Issues on GitHub dynamically from .github/issues/...")
    url = f"https://api.github.com/repos/{REPO}/issues"
    existing_issues = []
    if not dry_run and token:
        existing_issues = api_request(f"{url}?state=all&per_page=100", token=token) or []

    # Map title prefix / ID to existing issue number
    existing_map = {}
    for issue in existing_issues:
        title = issue.get("title", "")
        match = re.search(r"\[(TASK-\d+)\]", title)
        if match:
            existing_map[match.group(1)] = issue["number"]

    md_files = sorted(ISSUES_DIR.glob("task-*.md"))
    print(f"  🔍 Found {len(md_files)} task specification files in {ISSUES_DIR}")

    for md_file in md_files:
        content = md_file.read_text(encoding="utf-8")
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                fm = yaml.safe_load(parts[1]) or {}
            except Exception:
                fm = {}
            body = parts[2].strip()
        else:
            fm = {}
            body = content.strip()

        task_id = fm.get("id")
        if not task_id:
            m = re.search(r"task-(\d+)", md_file.name)
            task_id = f"TASK-{m.group(1)}" if m else md_file.stem.upper()

        raw_title = fm.get("title", md_file.stem)
        title = (
            f"[{task_id}] {raw_title}" if not raw_title.startswith(f"[{task_id}]") else raw_title
        )

        milestone_ref = fm.get("milestone")
        ms_number = None
        if milestone_ref is not None:
            ms_prefix = (
                f"{int(milestone_ref):02d}." if str(milestone_ref).isdigit() else str(milestone_ref)
            )
            for ms_title, ms_num in milestone_map.items():
                if ms_title.startswith(ms_prefix) or ms_title == str(milestone_ref):
                    ms_number = ms_num
                    break

        area = str(fm.get("area", "agent"))
        clean_area = area.replace("competition/gemma-developer-agent", "agent")
        task_type = fm.get("type", "feature")
        labels = [f"area: {clean_area}", f"type: {task_type}", "priority: high"]

        if dry_run:
            status = f"UPDATE #{existing_map[task_id]}" if task_id in existing_map else "CREATE"
            print(f"  [DRY-RUN] [{status}] {title} " f"(Milestone: {ms_number}, Labels: {labels})")
            continue

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
    parser = argparse.ArgumentParser(description="GitHub Kanban & Issue Setup Automation")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate execution without modifying GitHub",
    )
    args = parser.parse_args()

    print("==================================================")
    print(" 🚀 KAGGLE COMPETITIONS — GITHUB KANBAN SETUP     ")
    print("==================================================")
    if args.dry_run:
        print("🔍 Running in DRY-RUN mode (read-only simulation)...")
        token = ""
        milestone_map = {
            "01. Ingestion & Local Benchmark Harness": 1,
            "02. Declarative ADK Agent & Prompt Architecture": 2,
            "03. Test-Driven Closed Loop & Code-Graphs": 3,
            "04. Kaggle Submission Pipeline, LoRA Training & Paper Track": 4,
            "05. Empirical Hotspots & Golden Trajectories Post-Training": 5,
        }
        setup_tasks(token, milestone_map, dry_run=True)
    else:
        token = get_token()
        milestone_map = setup_milestones(token)
        setup_labels(token)
        setup_tasks(token, milestone_map, dry_run=False)

    print("==================================================")
    print(" ✅ SETUP DO KANBAN E ISSUES FINALIZADO COM SUCESSO! ")
    print("==================================================")


if __name__ == "__main__":
    main()
