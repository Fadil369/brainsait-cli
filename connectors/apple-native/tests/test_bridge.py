"""Unit tests for the Apple Bridge tool layer.

macOS CLIs are monkeypatched so the suite runs anywhere; what we verify is
the MCP surface: schemas, allowlist enforcement, gating, and pipeline chaining.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from brainsait_apple_bridge import config as config_module
from brainsait_apple_bridge import macos, server
from brainsait_apple_bridge.config import BridgeConfig


@pytest.fixture(autouse=True)
def fresh_config(tmp_path, monkeypatch):
    cfg = BridgeConfig()
    cfg.workflow_dirs = [tmp_path]
    monkeypatch.setattr(config_module, "CONFIG", cfg)
    return cfg


def call(tool: str, **kwargs) -> dict:
    result = asyncio.run(server.mcp.call_tool(tool, kwargs))
    return json.loads(result.content[0].text)


def fake_run(ok=True, stdout="", stderr="", rc=0):
    return macos.RunResult(ok, stdout, stderr, rc)


def test_tools_are_registered():
    tools = asyncio.run(server.mcp.list_tools())
    names = {t.name for t in tools}
    assert {
        "get_bridge_status",
        "list_shortcuts",
        "run_shortcut",
        "list_automator_workflows",
        "describe_automator_workflow",
        "run_automator_workflow",
        "run_applescript",
        "run_bridge_pipeline",
        "open_shortcut_in_editor",
    } <= names


def test_run_shortcut_success(monkeypatch):
    monkeypatch.setattr(macos, "run_shortcut", lambda name, inp, timeout: fake_run(stdout="42\n"))
    body = call("run_shortcut", name="Answer", input_text="question")
    assert body["ok"] and body["output"] == "42" and body["shortcut"] == "Answer"


def test_run_shortcut_allowlist(fresh_config, monkeypatch):
    fresh_config.allowed_shortcuts = ["Approved Only"]
    monkeypatch.setattr(macos, "run_shortcut", lambda *a, **k: fake_run(stdout="nope"))
    body = call("run_shortcut", name="Sneaky")
    assert not body["ok"] and "allowlist" in body["error"]


def test_run_shortcut_off_macos(monkeypatch):
    def boom(*a, **k):
        raise macos.MacOSUnavailableError("'shortcuts' was not found.")

    monkeypatch.setattr(macos, "run_shortcut", boom)
    body = call("run_shortcut", name="Anything")
    assert not body["ok"] and "not found" in body["error"]


def test_workflow_path_containment(fresh_config, tmp_path):
    outside = "/etc/evil.workflow"
    body = call("describe_automator_workflow", path=outside)
    assert not body["ok"] and "outside the allowed directories" in body["error"]


def test_run_automator_workflow(fresh_config, tmp_path, monkeypatch):
    wf = tmp_path / "Save Report.workflow"
    wf.mkdir()
    monkeypatch.setattr(
        macos, "run_automator_workflow", lambda w, i, v, timeout: fake_run(stdout="saved")
    )
    body = call("run_automator_workflow", path=str(wf), input_text="report body")
    assert body["ok"] and body["output"] == "saved"


def test_applescript_gated_by_default():
    body = call("run_applescript", script='return "hi"')
    assert not body["ok"] and "disabled" in body["error"]


def test_applescript_enabled(fresh_config, monkeypatch):
    fresh_config.allow_applescript = True
    monkeypatch.setattr(macos, "run_applescript", lambda s, timeout: fake_run(stdout="hi"))
    body = call("run_applescript", script='return "hi"')
    assert body["ok"] and body["output"] == "hi"


def test_pipeline_chains_output(fresh_config, tmp_path, monkeypatch):
    wf = tmp_path / "Stage2.workflow"
    wf.mkdir()
    seen_inputs = []

    def fake_shortcut(name, inp, timeout):
        seen_inputs.append(("shortcut", inp))
        return fake_run(stdout="from-shortcut")

    def fake_automator(w, inp, variables, timeout):
        seen_inputs.append(("automator", inp))
        return fake_run(stdout="from-automator")

    monkeypatch.setattr(macos, "run_shortcut", fake_shortcut)
    monkeypatch.setattr(macos, "run_automator_workflow", fake_automator)

    body = call(
        "run_bridge_pipeline",
        steps=[
            {"kind": "shortcut", "target": "Stage1"},
            {"kind": "automator", "target": str(wf)},
        ],
        initial_input="seed",
    )
    assert body["ok"]
    assert body["final_output"] == "from-automator"
    assert seen_inputs == [("shortcut", "seed"), ("automator", "from-shortcut")]


def test_pipeline_stops_on_failure(fresh_config, monkeypatch):
    monkeypatch.setattr(
        macos, "run_shortcut", lambda name, inp, timeout: fake_run(ok=False, stderr="boom", rc=1)
    )
    body = call("run_bridge_pipeline", steps=[{"kind": "shortcut", "target": "Broken"}])
    assert not body["ok"] and body["failed_step"] == 0
    assert body["trace"][0]["error"] == "boom"


def test_list_automator_workflows_finds_bundles(fresh_config, tmp_path):
    (tmp_path / "A.workflow").mkdir()
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "B.workflow").mkdir()
    body = call("list_automator_workflows")
    assert body["ok"] and body["count"] == 2


def test_describe_workflow_parses_actions(fresh_config, tmp_path):
    import plistlib

    wf = tmp_path / "Demo.workflow"
    (wf / "Contents").mkdir(parents=True)
    doc = {
        "actions": [
            {"action": {"AMActionName": "Run Shell Script", "AMBundleIdentifier": "com.apple.RunShellScript"}}
        ],
        "workflowMetaData": {"workflowTypeIdentifier": "com.apple.Automator.servicesMenu"},
    }
    with open(wf / "Contents" / "document.wflow", "wb") as fh:
        plistlib.dump(doc, fh)
    body = call("describe_automator_workflow", path=str(wf))
    assert body["ok"]
    assert body["actions"][0]["name"] == "Run Shell Script"
    assert body["type"] == "com.apple.Automator.servicesMenu"
