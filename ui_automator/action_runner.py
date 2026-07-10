import logging
import re
import time
from typing import Any, Dict, List, Optional

from .dump_manager import DumpManager
from .element_finder import ElementFinder
from .flow_loader import get_steps

logger = logging.getLogger(__name__)


class FlowRunner:
    def __init__(self, device):
        self.device = device
        self.dump_manager = DumpManager(device)
        self.element_finder = ElementFinder(device)
        self.context: Dict[str, Any] = {}
        self.flow_package: Optional[str] = None

    def _resolve_variable(self, path: str) -> Any:
        cursor = self.context
        for segment in path.split("."):
            if isinstance(cursor, dict) and segment in cursor:
                cursor = cursor[segment]
            elif isinstance(cursor, list) and segment.isdigit():
                idx = int(segment)
                cursor = cursor[idx] if 0 <= idx < len(cursor) else ""
            else:
                return ""
        return cursor

    def _resolve_text(self, value: Any) -> Any:
        if not isinstance(value, str) or "$" not in value:
            return value

        def _replace(match: re.Match) -> str:
            replacement = self._resolve_variable(match.group(1))
            return str(replacement)

        return re.sub(r"\$([a-zA-Z_][\w\.]*)", _replace, value)

    def _extract_text(self, element: Any) -> str:
        text = ""
        getter = getattr(element, "get_text", None)
        if callable(getter):
            text = getter()
        elif hasattr(element, "info") and isinstance(element.info, dict):
            text = element.info.get("text") or element.info.get("contentDescription") or element.info.get("description") or ""
        elif hasattr(element, "text"):
            text = element.text
        return str(text or "")

    def _store_variable(self, key: str, value: Any) -> None:
        if not key:
            return
        self.context[key] = value

    def _handle_failure(self, actions: Optional[List[str]]) -> None:
        if not actions:
            return

        for action in actions:
            if not isinstance(action, str):
                continue
            if action.startswith("delay:"):
                try:
                    seconds = float(action.split(":", 1)[1])
                    logger.info("Delaying for %s seconds due to failure action", seconds)
                    time.sleep(seconds)
                except ValueError:
                    logger.warning("Invalid delay value in on_failure: %s", action)
            elif action.startswith("log:"):
                logger.info(action.split(":", 1)[1])
            elif action.startswith("sleep:"):
                try:
                    seconds = float(action.split(":", 1)[1])
                    time.sleep(seconds)
                except ValueError:
                    logger.warning("Invalid sleep value in on_failure: %s", action)

    def _perform_action(self, step: Dict[str, Any]) -> Any:
        action = step.get("action")
        selector = step.get("selector", {})
        value = step.get("value")
        timeout = step.get("timeout", 15)

        logger.info("Performing action: %s", action)
        if action == "wait_for":
            return self.element_finder.wait_for(selector, timeout=timeout)
        if action == "tap":
            element = self.element_finder.find(selector, timeout=timeout)
            element.click()
            return element
        if action == "set_text":
            element = self.element_finder.find(selector, timeout=timeout)
            element.set_text(value or "")
            return element
        if action == "dump":
            return self.dump_manager.refresh_dump()
        if action == "press_back":
            self.device.press("back")
            return None
        if action == "sleep":
            time.sleep(int(value or 1))
            return None
        if action == "launch_app":
            package = step.get("package") or self.flow_package
            if not package:
                raise ValueError("No package specified for launch_app action")
            self.device.app_start(package)
            return {"launched": package}
        if action == "extract":
            element = self.element_finder.find(selector, timeout=timeout)
            text_value = self._extract_text(element)
            save_as = step.get("save_as")
            if save_as:
                self._store_variable(save_as, text_value)
            return text_value
        if action == "log":
            message = step.get("message") or ""
            message = self._resolve_text(message)
            logger.info(message)
            return message

        raise ValueError(f"Unsupported flow action: {action}")

    def run_flow(self, flow: Dict[str, Any]) -> List[Dict[str, Any]]:
        self.context = flow.get("variables", {}).copy() if isinstance(flow.get("variables"), dict) else {}
        self.flow_package = flow.get("package")
        if self.flow_package:
            logger.info("Launching flow package: %s", self.flow_package)
            self.device.app_start(self.flow_package)

        results: List[Dict[str, Any]] = []
        for step in get_steps(flow):
            step["value"] = self._resolve_text(step.get("value")) if step.get("value") else None
            step["message"] = self._resolve_text(step.get("message")) if step.get("message") else None
            try:
                result = self._perform_action(step)
            except Exception as error:
                logger.warning("Step failed '%s': %s", step.get("name") or step.get("action"), error)
                self._handle_failure(step.get("on_failure"))
                raise
            results.append({"step": step, "result": result})
        return results
