"""Ephemeral Workspace Sandbox Runner for SWE-bench Evaluation.

Provides isolated workspace execution environments for applying patches,
reading/writing files, and running hermetic pytest suites without contaminating
the host environment.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


@dataclass(frozen=True)
class SandboxResult:
    """Result of a command executed inside the sandbox.

    Attributes:
        exit_code: Process return code (0 = success).
        stdout: Standard output string.
        stderr: Standard error string.
        duration_seconds: Wall-clock execution time in seconds.
    """

    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float

    @property
    def is_success(self) -> bool:
        """Returns True if process exited with code 0."""
        return self.exit_code == 0


class SubprocessSandbox:
    """Subprocess-isolated workspace sandbox.

    Manages a dedicated temporary directory with its own git repository,
    allowing reproducible patch applications and test executions.
    """

    def __init__(
        self,
        workspace_dir: Optional[Path] = None,
        init_git: bool = True,
    ) -> None:
        """Initializes sandbox in given directory or creates a new temporary one.

        Args:
            workspace_dir: Optional explicit workspace path. If None, a temp dir is created.
            init_git: Whether to initialize a clean git repository if not present.
        """
        self._is_temp = workspace_dir is None
        if workspace_dir is None:
            self.workspace_dir = Path(tempfile.mkdtemp(prefix="swe_sandbox_"))
        else:
            self.workspace_dir = Path(workspace_dir)
            self.workspace_dir.mkdir(parents=True, exist_ok=True)

        if init_git:
            self._init_git_repo()

    def _init_git_repo(self) -> None:
        """Initializes a local git repository if one does not exist."""
        git_dir = self.workspace_dir / ".git"
        if not git_dir.exists():
            subprocess.run(
                ["git", "init"],
                cwd=self.workspace_dir,
                capture_output=True,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "SWE-Benchmark-Bot"],
                cwd=self.workspace_dir,
                capture_output=True,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.email", "bot@clean-chassis.org"],
                cwd=self.workspace_dir,
                capture_output=True,
                check=True,
            )

    def execute(
        self,
        cmd: Union[List[str], str],
        timeout: int = 120,
        env: Optional[Dict[str, str]] = None,
    ) -> SandboxResult:
        """Executes a command inside the workspace directory.

        Args:
            cmd: Command list or shell string.
            timeout: Maximum allowed execution time in seconds.
            env: Optional additional environment variables.

        Returns:
            SandboxResult with exit code, stdout, stderr, and duration.
        """
        exec_env = os.environ.copy()
        if env:
            exec_env.update(env)

        # Force unbuffered output and standard encoding
        exec_env["PYTHONUNBUFFERED"] = "1"
        exec_env["PYTHONDONTWRITEBYTECODE"] = "1"

        is_shell = isinstance(cmd, str)
        start_time = time.perf_counter()

        try:
            proc = subprocess.run(
                cmd,
                cwd=self.workspace_dir,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=is_shell,
                env=exec_env,
                check=False,
            )
            duration = time.perf_counter() - start_time
            return SandboxResult(
                exit_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                duration_seconds=duration,
            )
        except subprocess.TimeoutExpired as exc:
            duration = time.perf_counter() - start_time
            return SandboxResult(
                exit_code=124,
                stdout=exc.stdout or "" if isinstance(exc.stdout, str) else "",
                stderr=f"Command timed out after {timeout} seconds.",
                duration_seconds=duration,
            )
        except Exception as exc:
            duration = time.perf_counter() - start_time
            return SandboxResult(
                exit_code=1,
                stdout="",
                stderr=f"Sandbox execution error: {str(exc)}",
                duration_seconds=duration,
            )

    def write_file(self, relative_path: str, content: str) -> Path:
        """Writes content to a file inside the workspace safely.

        Args:
            relative_path: Target path relative to workspace root.
            content: Content string to write.

        Returns:
            Absolute Path to written file.

        Raises:
            ValueError: If path traversal outside workspace is detected.
        """
        target = (self.workspace_dir / relative_path).resolve()
        if not str(target).startswith(str(self.workspace_dir.resolve())):
            raise ValueError(f"Path traversal detected: {relative_path}")

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return target

    def read_file(self, relative_path: str) -> str:
        """Reads content of a file inside the workspace safely.

        Args:
            relative_path: Target path relative to workspace root.

        Returns:
            Content string.

        Raises:
            ValueError: If path traversal outside workspace is detected.
            FileNotFoundError: If target file does not exist.
        """
        target = (self.workspace_dir / relative_path).resolve()
        if not str(target).startswith(str(self.workspace_dir.resolve())):
            raise ValueError(f"Path traversal detected: {relative_path}")

        if not target.exists():
            raise FileNotFoundError(f"File not found in sandbox: {relative_path}")

        return target.read_text(encoding="utf-8")

    def apply_patch(self, patch: str) -> bool:
        """Applies a unified git diff patch with multi-pass fallback strategy.

        Args:
            patch: Unified diff patch text.

        Returns:
            True if patch was applied cleanly, False otherwise.
        """
        if not patch or not patch.strip():
            return False

        patch_file = self.workspace_dir / ".temp_patch.diff"
        patch_file.write_text(patch, encoding="utf-8")

        try:
            # Pass 1: Standard git apply
            res = self.execute(["git", "apply", "--whitespace=nowarn", str(patch_file)])
            if res.is_success:
                return True

            # Pass 2: git apply with recount (tolerant of line count discrepancies)
            res = self.execute(
                ["git", "apply", "--whitespace=nowarn", "--recount", str(patch_file)]
            )
            if res.is_success:
                return True

            # Pass 3: Fallback to GNU patch -p1
            res = self.execute(f"patch -p1 < {patch_file.name}")
            return res.is_success
        finally:
            if patch_file.exists():
                patch_file.unlink()

    def get_diff(self, base_ref: str = "HEAD") -> str:
        """Extracts unified diff of current changes against base reference.

        Args:
            base_ref: Git reference to diff against (default: 'HEAD').

        Returns:
            Unified diff string.
        """
        # Track untracked files without committing them
        self.execute(["git", "add", "-N", "."])
        res = self.execute(["git", "diff", "--binary", base_ref])
        return res.stdout

    def commit_all(self, message: str = "baseline") -> bool:
        """Stages and commits all current files to local git history.

        Args:
            message: Commit message.

        Returns:
            True if commit succeeded, False otherwise.
        """
        self.execute(["git", "add", "-A"])
        res = self.execute(["git", "commit", "-m", message, "--allow-empty"])
        return res.is_success

    def cleanup(self) -> None:
        """Deletes ephemeral workspace directory if created as temporary."""
        if self._is_temp and self.workspace_dir.exists():
            shutil.rmtree(self.workspace_dir, ignore_errors=True)

    def __enter__(self) -> SubprocessSandbox:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit with cleanup."""
        self.cleanup()
