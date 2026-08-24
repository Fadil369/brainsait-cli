"""Runtime configuration for the Apple Bridge, sourced from environment variables.

All knobs are environment-driven so the same package works unchanged as a
stdio server (Claude Desktop / Claude Code) and as a streamable-HTTP server
(claude.ai custom connector behind a tunnel).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _default_workflow_dirs() -> list[Path]:
    home = Path.home()
    return [
        home / "Library" / "Services",
        home / "Library" / "Workflows",
        home / "Documents" / "Automator",
    ]


@dataclass
class BridgeConfig:
    # Security -----------------------------------------------------------
    #: Shared secret required on HTTP requests. Empty disables HTTP auth
    #: (only sensible behind an authenticated tunnel such as Cloudflare Access).
    auth_token: str = ""
    #: If non-empty, only these shortcut names may be executed.
    allowed_shortcuts: list[str] = field(default_factory=list)
    #: Automator workflows may only be executed from inside these directories.
    workflow_dirs: list[Path] = field(default_factory=_default_workflow_dirs)
    #: Raw AppleScript execution is opt-in — it is arbitrary code execution.
    allow_applescript: bool = False

    # Execution ----------------------------------------------------------
    #: Default timeout (seconds) for a single Shortcuts/Automator run.
    timeout: float = 120.0
    #: Hard cap on tool-supplied timeouts.
    max_timeout: float = 600.0

    # HTTP transport -----------------------------------------------------
    host: str = "127.0.0.1"
    port: int = 8848
    #: Public hostnames (e.g. the tunnel host) allowed in the Host header.
    #: Empty disables DNS-rebinding host checks (token auth still applies).
    allowed_hosts: list[str] = field(default_factory=list)

    @classmethod
    def from_env(cls) -> "BridgeConfig":
        cfg = cls()
        cfg.auth_token = os.environ.get("APPLE_BRIDGE_TOKEN", "")
        cfg.allowed_shortcuts = _split_csv(os.environ.get("APPLE_BRIDGE_ALLOWED_SHORTCUTS", ""))
        extra_dirs = [
            Path(p).expanduser()
            for p in _split_csv(os.environ.get("APPLE_BRIDGE_WORKFLOW_DIRS", ""))
        ]
        cfg.workflow_dirs = _default_workflow_dirs() + extra_dirs
        cfg.allow_applescript = os.environ.get("APPLE_BRIDGE_ALLOW_APPLESCRIPT", "") in (
            "1",
            "true",
            "yes",
        )
        try:
            cfg.timeout = float(os.environ.get("APPLE_BRIDGE_TIMEOUT", cfg.timeout))
        except ValueError:
            pass
        cfg.host = os.environ.get("APPLE_BRIDGE_HOST", cfg.host)
        cfg.allowed_hosts = _split_csv(os.environ.get("APPLE_BRIDGE_ALLOWED_HOSTS", ""))
        try:
            cfg.port = int(os.environ.get("APPLE_BRIDGE_PORT", cfg.port))
        except ValueError:
            pass
        return cfg

    def clamp_timeout(self, requested: float | None) -> float:
        if requested is None or requested <= 0:
            return self.timeout
        return min(requested, self.max_timeout)

    def shortcut_allowed(self, name: str) -> bool:
        return not self.allowed_shortcuts or name in self.allowed_shortcuts

    def resolve_workflow(self, path: str) -> Path:
        """Resolve a workflow path and verify it lives inside an allowed directory."""
        candidate = Path(path).expanduser().resolve()
        for allowed in self.workflow_dirs:
            try:
                candidate.relative_to(allowed.expanduser().resolve())
                return candidate
            except ValueError:
                continue
        raise PermissionError(
            f"Workflow '{candidate}' is outside the allowed directories: "
            + ", ".join(str(d) for d in self.workflow_dirs)
            + ". Add its directory via APPLE_BRIDGE_WORKFLOW_DIRS."
        )


# Singleton used by the server; tests may replace it.
CONFIG = BridgeConfig.from_env()
