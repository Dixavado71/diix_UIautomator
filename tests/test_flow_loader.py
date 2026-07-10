import json
from pathlib import Path

from ui_automator.flow_loader import load_flow, normalize_step


def test_load_flow_from_dict(tmp_path):
    path = tmp_path / "flow.json"
    flow_data = {"steps": [{"action": "wait", "target": {"classe": "android.widget.TextView"}}]}
    path.write_text(json.dumps(flow_data), encoding="utf-8")

    flow = load_flow(str(path))
    assert flow["steps"][0]["action"] == "wait"


def test_normalize_step_with_target():
    step = {"action": "click", "target": {"texto_contem": "Entrar"}}
    normalized = normalize_step(step)

    assert normalized["action"] == "tap"
    assert normalized["selector"]["containsText"] == "Entrar"


def test_normalize_step_with_selector_aliases():
    step = {"action": "wait", "selector": {"texto_contem": "Entrar"}}
    normalized = normalize_step(step)

    assert normalized["action"] == "wait_for"
    assert normalized["selector"]["containsText"] == "Entrar"
