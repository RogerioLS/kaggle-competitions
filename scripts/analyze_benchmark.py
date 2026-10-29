"""Script to perform empirical analysis of the official Kaggle SWE-bench tasks.

Parses tasks.jsonl, computes repository distributions, patch size metrics,
hotspot files, and problem statement characteristics.
"""

from __future__ import annotations

import json
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TASKS_PATH = REPO_ROOT / "data" / "gemma-4-developer-agent" / "tasks.jsonl"


def parse_patch_details(patch_str: str) -> Tuple[List[str], int, int]:
    """Extracts modified file list, lines added, and lines deleted from unified diff."""
    files: List[str] = []
    lines_added = 0
    lines_deleted = 0
    current_file = None

    for line in patch_str.split("\n"):
        if line.startswith("diff --git") or line.startswith("--- a/"):
            m = re.search(r"--- a/(.+)", line)
            if m:
                current_file = m.group(1).strip()
                if current_file not in files:
                    files.append(current_file)
        elif line.startswith("+++ b/") and current_file is None:
            m = re.search(r"\+\+\+ b/(.+)", line)
            if m:
                current_file = m.group(1).strip()
                if current_file not in files:
                    files.append(current_file)
        elif line.startswith("+") and not line.startswith("+++"):
            lines_added += 1
        elif line.startswith("-") and not line.startswith("---"):
            lines_deleted += 1

    return files, lines_added, lines_deleted


def analyze_benchmark(tasks_file: Path) -> Dict[str, object]:
    """Runs empirical audit across all tasks in tasks.jsonl."""
    if not tasks_file.is_file():
        raise FileNotFoundError(f"tasks.jsonl not found at {tasks_file}")

    with open(tasks_file, "r", encoding="utf-8") as f:
        tasks = [json.loads(line) for line in f]

    total_tasks = len(tasks)
    repo_counts = Counter(t["repo"] for t in tasks)

    file_counts: List[int] = []
    lines_added_list: List[int] = []
    lines_deleted_list: List[int] = []
    total_changed_list: List[int] = []
    repo_files: Dict[str, Counter] = defaultdict(Counter)

    tasks_with_traceback = 0
    tasks_with_file_mention = 0

    for t in tasks:
        files, added, deleted = parse_patch_details(t.get("patch", ""))
        file_counts.append(len(files))
        lines_added_list.append(added)
        lines_deleted_list.append(deleted)
        total_changed_list.append(added + deleted)

        for f in files:
            repo_files[t["repo"]][f] += 1

        ps = t.get("problem_statement", "")
        if "Traceback" in ps or "Exception" in ps or "Error:" in ps:
            tasks_with_traceback += 1

        if any(
            (tf in ps or (len(tf.split("/")[-1]) > 4 and tf.split("/")[-1] in ps)) for tf in files
        ):
            tasks_with_file_mention += 1

    print("==================================================")
    print(" GEMMA 4 SWE-BENCH BENCHMARK EMPIRICAL REPORT     ")
    print("==================================================")
    print(f"Total Benchmark Tasks : {total_tasks}")
    print("\n[Repositories]")
    for repo, count in repo_counts.most_common():
        print(f"  {repo:<22}: {count:>3} ({count / total_tasks * 100:.1f}%)")

    print("\n[File Concentration per Task]")
    fc_dist = Counter(file_counts)
    for num_files, count in sorted(fc_dist.items()):
        pct = count / total_tasks * 100
        print(f"  {num_files:>2} file(s) modified: {count:>3} tasks ({pct:.1f}%)")

    print("\n[Patch Size Statistics]")
    print(f"  Median Additions    : {statistics.median(lines_added_list):.0f} lines")
    print(f"  Median Deletions    : {statistics.median(lines_deleted_list):.0f} lines")
    print(f"  Median Total Changed: {statistics.median(total_changed_list):.0f} lines")
    p75 = sorted(total_changed_list)[int(total_tasks * 0.75)]
    p90 = sorted(total_changed_list)[int(total_tasks * 0.90)]
    print(f"  P75 Total Changed   : {p75} lines")
    print(f"  P90 Total Changed   : {p90} lines")

    le15 = sum(1 for c in total_changed_list if c <= 15)
    le30 = sum(1 for c in total_changed_list if c <= 30)
    print(f"  Tasks with <= 15 lines: {le15} ({le15 / total_tasks * 100:.1f}%)")
    print(f"  Tasks with <= 30 lines: {le30} ({le30 / total_tasks * 100:.1f}%)")

    print("\n[Top Hotspot Files by Repository]")
    for repo, fcounts in repo_files.items():
        sub_total = repo_counts[repo]
        print(f"  Repo: {repo} ({sub_total} tasks)")
        for fpath, cnt in fcounts.most_common(5):
            print(f"    - {fpath:<38}: {cnt:>2} tasks ({cnt / sub_total * 100:.1f}%)")

    pure_loc = total_tasks - tasks_with_file_mention
    print("\n[Problem Statement Patterns]")
    print(
        f"  Contains Traceback/Exception   : {tasks_with_traceback} "
        f"({tasks_with_traceback / total_tasks * 100:.1f}%)"
    )
    print(
        f"  Explicit File Name Mentioned   : {tasks_with_file_mention} "
        f"({tasks_with_file_mention / total_tasks * 100:.1f}%)"
    )
    print(
        f"  Pure Localization Required     : {pure_loc} " f"({pure_loc / total_tasks * 100:.1f}%)"
    )
    print("==================================================")

    return {
        "total_tasks": total_tasks,
        "repo_counts": dict(repo_counts),
        "median_changed_lines": statistics.median(total_changed_list),
        "tasks_with_file_mention": tasks_with_file_mention,
    }


if __name__ == "__main__":
    analyze_benchmark(DEFAULT_TASKS_PATH)
