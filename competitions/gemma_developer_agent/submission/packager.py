"""Kaggle Submission Packager for Gemma 4 Developer Agent.

Packages the declarative agent specification, prompt templates, sub-agent configs,
and skill SOPs into a validated submission.zip adhering strictly to Kaggle rules:
- Root contains agent.yaml (declarative YAML specification)
- Zero raw Python entrypoints (agent.py or *.py disallowed in root)
- Deterministic ZIP archive structure with SHA256 manifests
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@dataclass
class PackagedFile:
    """Represents a single file packaged into submission.zip."""

    archive_path: str
    source_path: str
    size_bytes: int
    sha256: str


@dataclass
class Manifest:
    """Submission packaging manifest metadata."""

    submission_name: str
    timestamp_utc: str
    total_files: int
    uncompressed_size_bytes: int
    compressed_size_bytes: int
    archive_sha256: str
    files: List[PackagedFile]

    def to_json(self) -> str:
        """Serializes manifest to formatted JSON."""
        return json.dumps(asdict(self), indent=2)


class SubmissionPackager:
    """Builds and packages submission.zip for Kaggle Gemma 4 Developer Agent competition."""

    PROHIBITED_ROOT_EXTENSIONS = {".py", ".sh", ".bash", ".exe", ".bin"}
    PROHIBITED_ROOT_FILENAMES = {"agent.py", "main.py", "runner.py", "submission.py"}

    def __init__(
        self,
        base_dir: Optional[Path] = None,
        output_path: Optional[Path] = None,
        adapters_dir: Optional[Path] = None,
    ) -> None:
        """Initializes packager with repository paths.

        Args:
            base_dir: Base directory of gemma_developer_agent competition package.
            output_path: Target path for the output submission.zip file.
            adapters_dir: Optional path to LoRA adapters directory.
        """
        if base_dir is None:
            # Resolves competitions/gemma_developer_agent
            self.base_dir = Path(__file__).resolve().parent.parent
        else:
            self.base_dir = Path(base_dir).resolve()

        if output_path is None:
            # Default to repo root / artifacts / submission.zip
            repo_root = self.base_dir.parent.parent
            self.output_path = repo_root / "artifacts" / "submission.zip"
        else:
            self.output_path = Path(output_path).resolve()

        self.agent_dir = self.base_dir / "agent"
        self.prompts_dir = self.base_dir / "prompts"
        self.skills_dir = self.base_dir / "skills"

        if adapters_dir is not None:
            self.adapters_dir = Path(adapters_dir).resolve()
        elif (self.base_dir / "adapters").is_dir():
            self.adapters_dir = self.base_dir / "adapters"
        elif (self.output_path.parent / "adapters").is_dir():
            self.adapters_dir = self.output_path.parent / "adapters"
        else:
            self.adapters_dir = self.base_dir / "adapters"

    @staticmethod
    def compute_sha256(file_path: Path) -> str:
        """Computes SHA256 hexadecimal hash for a file."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def collect_files_to_package(self) -> List[Tuple[Path, str]]:
        """Discovers and maps source files to their relative archive paths.

        Returns:
            List of tuples mapping (source_path, archive_relative_path).

        Raises:
            FileNotFoundError: If required agent.yaml or prompts are missing.
        """
        entries: List[Tuple[Path, str]] = []

        # 1. Root agent.yaml (MANDATORY)
        agent_yaml = self.agent_dir / "agent.yaml"
        if not agent_yaml.is_file():
            # Check fallback in base_dir
            if (self.base_dir / "agent.yaml").is_file():
                agent_yaml = self.base_dir / "agent.yaml"
            else:
                raise FileNotFoundError(f"Mandatory agent.yaml missing at {agent_yaml}")
        entries.append((agent_yaml, "agent.yaml"))

        # 1b. Root eval_config.yaml (official swegemma evaluation budget configuration)
        eval_config_yaml = self.agent_dir / "eval_config.yaml"
        if not eval_config_yaml.is_file() and (self.base_dir / "eval_config.yaml").is_file():
            eval_config_yaml = self.base_dir / "eval_config.yaml"
        if eval_config_yaml.is_file():
            entries.append((eval_config_yaml, "eval_config.yaml"))

        # 2. Configs (sampling.yaml)
        configs_dir = self.agent_dir / "configs"
        if configs_dir.is_dir():
            for cfg in sorted(configs_dir.glob("*.yaml")):
                entries.append((cfg, f"configs/{cfg.name}"))

        # 3. Sub-agents (*.yaml)
        sub_agents_dir = self.agent_dir / "sub_agents"
        if sub_agents_dir.is_dir():
            for sa in sorted(sub_agents_dir.glob("*.yaml")):
                entries.append((sa, f"sub_agents/{sa.name}"))

        # 4. Prompts (*.md)
        if self.prompts_dir.is_dir():
            for p in sorted(self.prompts_dir.glob("*.md")):
                entries.append((p, f"prompts/{p.name}"))

        # 5. Skills (*.md or subdirectories)
        if self.skills_dir.is_dir():
            for skill_path in sorted(self.skills_dir.rglob("*.md")):
                rel = skill_path.relative_to(self.skills_dir)
                entries.append((skill_path, f"skills/{rel.as_posix()}"))

        # 6. Adapters (optional LoRA weights)
        if self.adapters_dir.is_dir():
            for adapter_file in sorted(self.adapters_dir.rglob("*")):
                if adapter_file.is_file():
                    rel = adapter_file.relative_to(self.adapters_dir)
                    entries.append((adapter_file, f"adapters/{rel.as_posix()}"))

        return entries

    def validate_pre_packaging(self, entries: List[Tuple[Path, str]]) -> None:
        """Enforces competition packaging constraints before creating zip.

        Raises:
            ValueError: If prohibited entrypoints or illegal file structures are found.
        """
        root_files = {arc for _, arc in entries if "/" not in arc}

        if "agent.yaml" not in root_files:
            raise ValueError("Kaggle specification requires 'agent.yaml' at root of submission.")

        for _, arc in entries:
            # Check prohibited files at root
            if "/" not in arc:
                if arc in self.PROHIBITED_ROOT_FILENAMES:
                    raise ValueError(
                        f"Prohibited entrypoint found in root: '{arc}'. "
                        "Python execution files are rejected by the Kaggle YAML compiler."
                    )
                ext = Path(arc).suffix.lower()
                if ext in self.PROHIBITED_ROOT_EXTENSIONS:
                    raise ValueError(
                        f"Prohibited file extension '{ext}' in root for '{arc}'. "
                        "Submissions must be strictly declarative YAML/Markdown."
                    )

    def create_package(self, dry_run: bool = False) -> Manifest:
        """Packages files into submission.zip with compression and metadata manifest.

        Args:
            dry_run: If True, calculates manifest without writing zip to disk.

        Returns:
            Manifest object containing package statistics and file hashes.
        """
        from datetime import datetime, timezone

        entries = self.collect_files_to_package()
        self.validate_pre_packaging(entries)

        packaged_files: List[PackagedFile] = []
        total_uncompressed = 0

        for src, arc in entries:
            size = src.stat().st_size
            sha = self.compute_sha256(src)
            packaged_files.append(
                PackagedFile(
                    archive_path=arc,
                    source_path=str(src),
                    size_bytes=size,
                    sha256=sha,
                )
            )
            total_uncompressed += size

        if dry_run:
            return Manifest(
                submission_name=self.output_path.name,
                timestamp_utc=datetime.now(timezone.utc).isoformat(),
                total_files=len(packaged_files),
                uncompressed_size_bytes=total_uncompressed,
                compressed_size_bytes=0,
                archive_sha256="dry-run-skipped",
                files=packaged_files,
            )

        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write ZIP archive
        with zipfile.ZipFile(
            self.output_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
        ) as zf:
            for src, arc in entries:
                zf.write(src, arcname=arc)

        compressed_size = self.output_path.stat().st_size
        archive_sha = self.compute_sha256(self.output_path)

        manifest = Manifest(
            submission_name=self.output_path.name,
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            total_files=len(packaged_files),
            uncompressed_size_bytes=total_uncompressed,
            compressed_size_bytes=compressed_size,
            archive_sha256=archive_sha,
            files=packaged_files,
        )

        manifest_path = self.output_path.parent / "submission_manifest.json"
        manifest_path.write_text(manifest.to_json(), encoding="utf-8")

        return manifest


def package_submission(
    output_path: Optional[Path] = None,
    adapters_dir: Optional[Path] = None,
    dry_run: bool = False,
) -> Tuple[Path, Manifest]:
    """Convenience helper to package submission.zip and return output path and manifest."""
    packager = SubmissionPackager(output_path=output_path, adapters_dir=adapters_dir)
    manifest = packager.create_package(dry_run=dry_run)
    return packager.output_path, manifest


def main() -> int:
    """CLI entrypoint for packaging Kaggle submission."""
    parser = argparse.ArgumentParser(
        description="Builds and validates Kaggle submission.zip for Gemma 4 Developer Agent."
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Target path for submission.zip (default: artifacts/submission.zip)",
    )
    parser.add_argument(
        "--adapters-dir",
        type=str,
        default=None,
        help="Optional path to LoRA adapters directory to package.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate packaging and print manifest without creating archive.",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Run validator and dry-run execution immediately after packaging.",
    )

    args = parser.parse_args()

    try:
        out_path = Path(args.output) if args.output else None
        ad_path = Path(args.adapters_dir) if args.adapters_dir else None
        target_path, manifest = package_submission(
            output_path=out_path, adapters_dir=ad_path, dry_run=args.dry_run
        )

        mode = "[DRY-RUN] " if args.dry_run else ""
        print(f"📦 {mode}Submission Packaging Summary:")
        print(f"  Destination : {target_path}")
        print(f"  Files count : {manifest.total_files}")
        print(f"  Uncompressed: {manifest.uncompressed_size_bytes:,} bytes")
        if not args.dry_run:
            print(f"  Compressed  : {manifest.compressed_size_bytes:,} bytes")
            print(f"  SHA256      : {manifest.archive_sha256}")
        print("\n  Manifest file listing:")
        for pf in manifest.files:
            print(f"    - {pf.archive_path} ({pf.size_bytes} B) [{pf.sha256[:10]}]")

        if args.validate and not args.dry_run:
            from competitions.gemma_developer_agent.submission.validator import (
                validate_submission,
                verify_submission_dry_run,
            )

            print("\n🔍 Running automated validation on generated archive...")
            report = validate_submission(target_path)
            if not report.passed:
                print(f"❌ Validation failed: {report.errors}")
                return 1
            print("✔ Structure and offline constraints passed!")

            print("🚀 Executing submission dry-run on synthetic SWE-bench instance...")
            dry_ok = verify_submission_dry_run(target_path)
            if not dry_ok:
                print("❌ Dry-run execution failed.")
                return 1
            print("✔ Dry-run execution succeeded!")

        return 0

    except Exception as exc:
        print(f"❌ Error packaging submission: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
