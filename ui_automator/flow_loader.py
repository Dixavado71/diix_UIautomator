import json
from pathlib import Path
from typing import Any, Dict, List

TARGET_KEY_MAP = {
    "classe": "className",
    "class": "className",
    "resource_id": "resourceId",
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
    "find_all": "find_all",
    "tap_all": "tap_all",
    "wait_any": "wait_for_any",
    "return": "return",
    "if": "if",
    "loop": "loop",
}


def load_flow(path: str) -> Dict[str, Any]:
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        flow = json.load(handle)

    if isinstance(flow, list):
        flow = {"steps": flow}

    if "steps" not in flow:
        raise ValueError("Flow file must contain a top-level 'steps' array")

    flow["_flow_path"] = str(config_path.resolve())
    return flow


def _normalize_target(target: Any) -> Any:
    if isinstance(target, dict):
        selector: Dict[str, Any] = {}
        for key, value in target.items():
            if value is None:
                continue
            mapped = TARGET_KEY_MAP.get(key, key)
            selector[mapped] = value
        return selector
    if isinstance(target, list):
        return [_normalize_target(item) for item in target if isinstance(item, (dict, list))]
    return {}


def _normalize_selector(selector: Any) -> Any:
    return _normalize_target(selector)


def normalize_step(step: Dict[str, Any]) -> Dict[str, Any]:
    action = step.get("action")
    normalized_action = ACTION_MAP.get(action, action)
    selector = _normalize_selector(step.get("selector")) if step.get("selector") is not None else _normalize_target(step.get("target", {}))

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
        "over": step.get("over"),
        "var_name": step.get("var_name"),
        "back_after_each": step.get("back_after_each", False),
        "steps": step.get("steps", []),
        "condicao": step.get("condicao") or step.get("condition"),
        "then": step.get("then", []),
        "else": step.get("else", []),
        "seconds": step.get("seconds"),
        "retries": step.get("retries", 0),
        "retry_delay": step.get("retry_delay", 0.2),
    }
    return normalized


def get_steps(flow: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [normalize_step(step) for step in flow.get("steps", [])]
