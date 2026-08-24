"""MCP tool surface for the BrainSAIT Apple Bridge.

Exposes Apple Shortcuts and Automator to Claude, plus a pipeline tool that
chains the two apps together — the actual Shortcuts ↔ Automator bridge.
"""

from __future__ import annotations

import json
from typing import Literal

from mcp.server.mcpserver import MCPServer
from pydantic import BaseModel, Field

from . import config as config_module
from . import macos

mcp = MCPServer(
    "brainsait-apple-bridge",
    instructions=(
        "Bridge between Claude and the Apple automation stack on this Mac. "
        "Use list_shortcuts / list_automator_workflows to discover what exists, "
        "run_shortcut / run_automator_workflow to execute a single automation, and "
        "run_bridge_pipeline to chain Shortcuts and Automator steps, feeding each "
        "step's output into the next. Call get_bridge_status first if a tool "
        "reports that macOS CLIs are unavailable."
    ),
)


def _cfg() -> config_module.BridgeConfig:
    return config_module.CONFIG


def _payload(result: macos.RunResult, **extra) -> str:
    body = {
        "ok": result.ok,
        "output": result.stdout.strip(),
        "error": result.stderr.strip(),
        "returncode": result.returncode,
        **extra,
    }
    return json.dumps(body, ensure_ascii=False)


# --- Discovery ------------------------------------------------------------


@mcp.tool()
def get_bridge_status() -> str:
    """Report whether the bridge is running on macOS and which Apple CLIs are available,
    plus the active security configuration (allowlists, AppleScript gate)."""
    cfg = _cfg()
    body = {
        **macos.status(),
        "allowed_shortcuts": cfg.allowed_shortcuts or "all",
        "workflow_dirs": [str(d) for d in cfg.workflow_dirs],
        "applescript_enabled": cfg.allow_applescript,
        "default_timeout_seconds": cfg.timeout,
    }
    return json.dumps(body, ensure_ascii=False)


@mcp.tool()
def list_shortcuts(folder: str | None = None) -> str:
    """List the Shortcuts available on this Mac, one per line with its identifier.

    Args:
        folder: Optional Shortcuts folder name to filter by.
    """
    try:
        return _payload(macos.list_shortcuts(folder))
    except macos.MacOSUnavailableError as exc:
        return json.dumps({"ok": False, "error": str(exc)})


@mcp.tool()
def list_automator_workflows() -> str:
    """List Automator workflow bundles (.workflow) found in the allowed directories
    (Quick Actions in ~/Library/Services, plus any APPLE_BRIDGE_WORKFLOW_DIRS)."""
    cfg = _cfg()
    workflows = macos.find_workflows(cfg.workflow_dirs)
    return json.dumps(
        {
            "ok": True,
            "count": len(workflows),
            "workflows": [str(w) for w in workflows],
            "searched_dirs": [str(d) for d in cfg.workflow_dirs],
        },
        ensure_ascii=False,
    )


@mcp.tool()
def describe_automator_workflow(path: str) -> str:
    """Summarize an Automator workflow: its type and the ordered list of actions inside it.

    Args:
        path: Path to a .workflow bundle (must be inside an allowed directory).
    """
    cfg = _cfg()
    try:
        workflow = cfg.resolve_workflow(path)
    except PermissionError as exc:
        return json.dumps({"ok": False, "error": str(exc)})
    return json.dumps({"ok": True, **macos.describe_workflow(workflow)}, ensure_ascii=False)


# --- Execution ------------------------------------------------------------


@mcp.tool()
def run_shortcut(name: str, input_text: str | None = None, timeout_seconds: float | None = None) -> str:
    """Run an Apple Shortcut by name and return its text output.

    Args:
        name: Exact shortcut name as shown in the Shortcuts app.
        input_text: Optional text passed to the shortcut as its input.
        timeout_seconds: Optional per-run timeout (capped by server config).
    """
    cfg = _cfg()
    if not cfg.shortcut_allowed(name):
        return json.dumps(
            {
                "ok": False,
                "error": f"Shortcut '{name}' is not in the allowlist "
                "(APPLE_BRIDGE_ALLOWED_SHORTCUTS).",
            }
        )
    try:
        result = macos.run_shortcut(name, input_text, timeout=cfg.clamp_timeout(timeout_seconds))
    except macos.MacOSUnavailableError as exc:
        return json.dumps({"ok": False, "error": str(exc)})
    return _payload(result, shortcut=name)


@mcp.tool()
def run_automator_workflow(
    path: str,
    input_text: str | None = None,
    variables: dict[str, str] | None = None,
    timeout_seconds: float | None = None,
) -> str:
    """Run an Automator workflow (.workflow bundle) and return its output.

    Args:
        path: Path to the workflow bundle, inside an allowed directory.
        input_text: Optional text piped to the workflow as input.
        variables: Optional Automator variable overrides (name -> value).
        timeout_seconds: Optional per-run timeout (capped by server config).
    """
    cfg = _cfg()
    try:
        workflow = cfg.resolve_workflow(path)
        result = macos.run_automator_workflow(
            workflow, input_text, variables, timeout=cfg.clamp_timeout(timeout_seconds)
        )
    except PermissionError as exc:
        return json.dumps({"ok": False, "error": str(exc)})
    except macos.MacOSUnavailableError as exc:
        return json.dumps({"ok": False, "error": str(exc)})
    return _payload(result, workflow=str(workflow))


@mcp.tool()
def run_applescript(script: str, timeout_seconds: float | None = None) -> str:
    """Run raw AppleScript (osascript). Disabled unless APPLE_BRIDGE_ALLOW_APPLESCRIPT=1,
    because this is arbitrary code execution on the Mac.

    Args:
        script: The AppleScript source to execute.
        timeout_seconds: Optional per-run timeout (capped by server config).
    """
    cfg = _cfg()
    if not cfg.allow_applescript:
        return json.dumps(
            {
                "ok": False,
                "error": "AppleScript execution is disabled. Set APPLE_BRIDGE_ALLOW_APPLESCRIPT=1 "
                "on the server to enable it.",
            }
        )
    try:
        result = macos.run_applescript(script, timeout=cfg.clamp_timeout(timeout_seconds))
    except macos.MacOSUnavailableError as exc:
        return json.dumps({"ok": False, "error": str(exc)})
    return _payload(result)


@mcp.tool()
def open_shortcut_in_editor(name: str) -> str:
    """Open a shortcut in the Shortcuts editor on the Mac (GUI action, no output)."""
    try:
        return _payload(macos.open_shortcut_in_editor(name), shortcut=name)
    except macos.MacOSUnavailableError as exc:
        return json.dumps({"ok": False, "error": str(exc)})


# --- The bridge: chained pipelines ---------------------------------------


class PipelineStep(BaseModel):
    """One step in a Shortcuts ↔ Automator pipeline."""

    kind: Literal["shortcut", "automator", "applescript"] = Field(
        description="Which engine runs this step."
    )
    target: str = Field(
        description="Shortcut name, Automator workflow path, or AppleScript source."
    )
    use_previous_output: bool = Field(
        default=True,
        description="Feed the previous step's output into this step as its input.",
    )
    variables: dict[str, str] | None = Field(
        default=None, description="Automator variable overrides (automator steps only)."
    )


@mcp.tool()
def run_bridge_pipeline(steps: list[PipelineStep], initial_input: str | None = None) -> str:
    """Chain Shortcuts and Automator into one native pipeline: run each step in order,
    passing the previous step's text output as the next step's input.

    Example: [{kind: "shortcut", target: "Fetch Inbox Summary"},
              {kind: "automator", target: "~/Library/Services/Save Report.workflow"}]

    Args:
        steps: Ordered steps; each runs a shortcut, an Automator workflow, or AppleScript.
        initial_input: Optional text fed into the first step.
    """
    cfg = _cfg()
    current: str | None = initial_input
    trace: list[dict] = []
    for index, step in enumerate(steps):
        step_input = current if step.use_previous_output else None
        try:
            if step.kind == "shortcut":
                if not cfg.shortcut_allowed(step.target):
                    raise PermissionError(f"Shortcut '{step.target}' is not in the allowlist.")
                result = macos.run_shortcut(step.target, step_input, timeout=cfg.timeout)
            elif step.kind == "automator":
                workflow = cfg.resolve_workflow(step.target)
                result = macos.run_automator_workflow(
                    workflow, step_input, step.variables, timeout=cfg.timeout
                )
            else:  # applescript
                if not cfg.allow_applescript:
                    raise PermissionError(
                        "AppleScript steps are disabled (APPLE_BRIDGE_ALLOW_APPLESCRIPT)."
                    )
                result = macos.run_applescript(step.target, timeout=cfg.timeout)
        except (PermissionError, macos.MacOSUnavailableError) as exc:
            trace.append({"step": index, "kind": step.kind, "target": step.target, "ok": False, "error": str(exc)})
            return json.dumps({"ok": False, "failed_step": index, "trace": trace}, ensure_ascii=False)

        trace.append(
            {
                "step": index,
                "kind": step.kind,
                "target": step.target,
                "ok": result.ok,
                "output": result.stdout.strip(),
                "error": result.stderr.strip(),
            }
        )
        if not result.ok:
            return json.dumps({"ok": False, "failed_step": index, "trace": trace}, ensure_ascii=False)
        current = result.stdout.strip()

    return json.dumps({"ok": True, "final_output": current or "", "trace": trace}, ensure_ascii=False)
