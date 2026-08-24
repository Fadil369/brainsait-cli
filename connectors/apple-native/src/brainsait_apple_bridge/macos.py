"""Thin, testable wrappers around the macOS automation CLIs.

Everything that touches `shortcuts`, `automator`, `osascript`, or `open`
lives here so the MCP tool layer stays pure and unit-testable off-macOS.
"""

from __future__ import annotations

import plistlib
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


class MacOSUnavailableError(RuntimeError):
    """Raised when a required macOS CLI is missing (i.e., not running on a Mac)."""


@dataclass
class RunResult:
    ok: bool
    stdout: str
    stderr: str
    returncode: int


def is_macos() -> bool:
    return sys.platform == "darwin"


def _require(binary: str) -> str:
    path = shutil.which(binary)
    if not path:
        raise MacOSUnavailableError(
            f"'{binary}' was not found. The Apple Bridge must run on macOS "
            "(the machine where Shortcuts and Automator live), not on a remote server."
        )
    return path


def _run(args: list[str], *, input_text: str | None = None, timeout: float = 120.0) -> RunResult:
    try:
        proc = subprocess.run(
            args,
            input=input_text,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return RunResult(False, "", f"Timed out after {timeout:.0f}s: {' '.join(args)}", -1)
    return RunResult(proc.returncode == 0, proc.stdout, proc.stderr, proc.returncode)


# --- Shortcuts ------------------------------------------------------------


def list_shortcuts(folder: str | None = None, timeout: float = 30.0) -> RunResult:
    args = [_require("shortcuts"), "list", "--show-identifiers"]
    if folder:
        args += ["--folder-name", folder]
    return _run(args, timeout=timeout)


def run_shortcut(name: str, input_text: str | None = None, timeout: float = 120.0) -> RunResult:
    """Run a shortcut, capturing its output via temp files.

    `shortcuts run` only reliably emits output through --output-path, so we
    round-trip input/output through a private temp directory.
    """
    binary = _require("shortcuts")
    with tempfile.TemporaryDirectory(prefix="brainsait-bridge-") as tmp:
        out_path = Path(tmp) / "output.txt"
        args = [binary, "run", name, "--output-path", str(out_path), "--output-type", "public.plain-text"]
        if input_text is not None:
            in_path = Path(tmp) / "input.txt"
            in_path.write_text(input_text, encoding="utf-8")
            args += ["--input-path", str(in_path)]
        result = _run(args, timeout=timeout)
        if out_path.exists():
            captured = out_path.read_text(encoding="utf-8", errors="replace")
            result = RunResult(result.ok, captured or result.stdout, result.stderr, result.returncode)
        return result


def open_shortcut_in_editor(name: str, timeout: float = 15.0) -> RunResult:
    return _run([_require("shortcuts"), "view", name], timeout=timeout)


# --- Automator ------------------------------------------------------------


def run_automator_workflow(
    workflow: Path,
    input_text: str | None = None,
    variables: dict[str, str] | None = None,
    timeout: float = 120.0,
) -> RunResult:
    args = [_require("automator")]
    if input_text is not None:
        args += ["-i", "-"]  # read workflow input from stdin
    for key, value in (variables or {}).items():
        args += ["-D", f"{key}={value}"]
    args.append(str(workflow))
    return _run(args, input_text=input_text, timeout=timeout)


def find_workflows(dirs: list[Path]) -> list[Path]:
    found: list[Path] = []
    for base in dirs:
        base = base.expanduser()
        if not base.is_dir():
            continue
        found += sorted(base.rglob("*.workflow"))
    # De-duplicate while preserving order
    seen: set[Path] = set()
    unique = []
    for p in found:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return unique


def describe_workflow(workflow: Path) -> dict:
    """Best-effort summary of a .workflow bundle from its document.wflow plist."""
    doc = workflow / "Contents" / "document.wflow"
    info: dict = {"path": str(workflow), "name": workflow.stem, "actions": []}
    if not doc.is_file():
        info["error"] = "document.wflow not found inside the bundle"
        return info
    try:
        with open(doc, "rb") as fh:
            data = plistlib.load(fh)
    except Exception as exc:  # malformed plist — report, don't crash
        info["error"] = f"could not parse workflow plist: {exc}"
        return info
    for entry in data.get("actions", []):
        action = entry.get("action", {})
        info["actions"].append(
            {
                "name": action.get("AMActionName") or action.get("ActionName") or action.get("AMBundleIdentifier", "unknown"),
                "bundle_id": action.get("AMBundleIdentifier", ""),
            }
        )
    wf_meta = data.get("workflowMetaData", {})
    if wf_meta.get("workflowTypeIdentifier"):
        info["type"] = wf_meta["workflowTypeIdentifier"]
    return info


# --- AppleScript ----------------------------------------------------------


def run_applescript(script: str, timeout: float = 60.0) -> RunResult:
    """Run an AppleScript passed on stdin (avoids shell-quoting pitfalls)."""
    return _run([_require("osascript"), "-"], input_text=script, timeout=timeout)


def status() -> dict:
    return {
        "platform": sys.platform,
        "is_macos": is_macos(),
        "shortcuts_cli": shutil.which("shortcuts"),
        "automator_cli": shutil.which("automator"),
        "osascript_cli": shutil.which("osascript"),
    }
