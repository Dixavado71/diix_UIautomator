import json
from pathlib import Path
from typing import Any, Dict, List

TARGET_KEY_MAP = {
    "classe": "className",
    "resourceId": "resourceId",
    "texto": "text",
    "texto_contem": "containsText",
    "descricao": "description",
    "descricao_contem": "containsDescription",
    "description": "description",
    "className": "className",
    "text": "text",
}

ACTION_MAP = {
    "wait": "wait_for",
    "click": "tap",
    "tap": "tap",
    "type": "set_text",
    "input": "set_text",
    "sleep": "sleep",
    "delay": "sleep",
    "press_back": "press_back",
    "back": "press_back",
    "extract": "extract",
    "log": "log",
    "launch_app": "launch_app",
    "dump": "dump",
}


def load_flow(path: str) -> Dict[str, Any]:
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        flow = json.load(handle)

    if isinstance(flow, list):
        return {"steps": flow}

    if "steps" not in flow:
        raise ValueError("Flow file must contain a top-level 'steps' array")

    return flow


def _normalize_target(target: Dict[str, Any]) -> Dict[str, Any]:
    selector: Dict[str, Any] = {}
    for key, value in (target or {}).items():
        if value is None:
            continue
        mapped = TARGET_KEY_MAP.get(key, key)
        selector[mapped] = value
    return selector


def normalize_step(step: Dict[str, Any]) -> Dict[str, Any]:
    action = step.get("action")
    normalized_action = ACTION_MAP.get(action, action)
    selector = step.get("selector") if step.get("selector") else _normalize_target(step.get("target", {}))

    normalized = {
        "name": step.get("name"),
        "action": normalized_action,
        "selector": selector,
        "value": step.get("value"),
        "timeout": step.get("timeout", 15),
        "description": step.get("description"),
        "package": step.get("package"),
        "save_as": step.get("save_as"),
        "continue_on_failure": step.get("continue_on_failure", False),
        "on_failure": step.get("on_failure", []),
        "message": step.get("message") or step.get("mensagem"),
    }
    return normalized


def get_steps(flow: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [normalize_step(step) for step in flow.get("steps", [])]
