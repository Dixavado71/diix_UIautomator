import logging
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .dump_manager import DumpManager
from .element_finder import ElementFinder
from .flow_loader import get_steps, normalize_step

logger = logging.getLogger(__name__)


class FlowReturn(Exception):
    def __init__(self, value: Any):
        super().__init__("Flow returned")
        self.value = value


class FlowRunner:
    def __init__(self, device):
        self.device = device
        self.dump_manager = DumpManager(device)
        self.element_finder = ElementFinder(device)
        self.context: Dict[str, Any] = {}
        self.flow_package: Optional[str] = None
        self.flow_path: Optional[Path] = None

    def _resolve_variable(self, path: str) -> Any:
        cursor = self.context
        for segment in path.split('.'):
            if isinstance(cursor, dict) and segment in cursor:
                cursor = cursor[segment]
            elif isinstance(cursor, list) and segment.isdigit():
                idx = int(segment)
                cursor = cursor[idx] if 0 <= idx < len(cursor) else ""
            else:
                return ""
        return cursor

    def _resolve_text(self, value: Any) -> Any:
        if not isinstance(value, str) or '$' not in value:
            return value

        if value.strip().startswith('$') and re.fullmatch(r"\$[a-zA-Z_][\w\.]*", value.strip()):
            variable = value.strip()[1:]
            return self._resolve_variable(variable)

        def _replace(match: re.Match) -> str:
            replacement = self._resolve_variable(match.group(1))
            return str(replacement)

        return re.sub(r"\$([a-zA-Z_][\w\.]*)", _replace, value)

    def _resolve_data(self, data: Any) -> Any:
        if isinstance(data, str):
            return self._resolve_text(data)
        if isinstance(data, dict):
            return {key: self._resolve_data(value) for key, value in data.items()}
        if isinstance(data, list):
            return [self._resolve_data(value) for value in data]
        return data

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

    def _load_file_variables(self, flow: Dict[str, Any]) -> None:
        if not isinstance(flow.get("variables"), dict):
            return

        for key, value in list(self.context.items()):
            if not key.endswith("_file") or not isinstance(value, str):
                continue
            target_key = key[: -len("_file")]
            if not target_key:
                continue
            if target_key in self.context and self.context[target_key]:
                continue
            file_path = Path(value)
            if not file_path.is_absolute() and self.flow_path is not None:
                file_path = self.flow_path.parent / file_path
            try:
                raw_text = file_path.read_text(encoding="utf-8")
            except FileNotFoundError:
                raise RuntimeError(f"Flow variable file not found: {file_path}")
            self.context[target_key] = [line.strip() for line in raw_text.splitlines() if line.strip()]

    def _condition_met(self, condition: Dict[str, Any], timeout: int = 10) -> bool:
        if not condition:
            return False
        return self.element_finder.exists(condition, timeout=timeout)

    def _perform_action(self, step: Dict[str, Any]) -> Any:
        action = step.get("action")
        selector = step.get("selector", {})
        value = step.get("value")
        timeout = step.get("timeout", 15)

        logger.info("Performing action: %s", action)
        if action == "wait_for":
            try:
                return self.element_finder.wait_for(selector, timeout=timeout)
            except Exception:
                # fallback: poll for any matching elements and return first
                elements = self._poll_find_all(selector, timeout=timeout)
                if elements:
                    return elements[0]
                raise
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
            seconds = value if value is not None else step.get("seconds")
            try:
                sleep_seconds = float(seconds or 1)
            except (TypeError, ValueError):
                sleep_seconds = 1.0
            time.sleep(sleep_seconds)
            return None
        if action == "launch_app":
            package = step.get("package") or self.flow_package
            if not package:
                raise ValueError("No package specified for launch_app action")
            self.device.app_start(package)
            return {"launched": package}
        if action == "extract":
            try:
                element = self.element_finder.find(selector, timeout=timeout)
            except Exception:
                # fallback: try find_all and pick the first element
                elements = []
                try:
                    elements = self.element_finder.find_all(selector, timeout=timeout)
                except Exception:
                    elements = []
                if elements:
                    element = elements[0]
                else:
                    raise

            text_value = self._extract_text(element)
            save_as = step.get("save_as")
            if save_as:
                self._store_variable(save_as, text_value)
            return text_value
        if action == "find_all":
            elements = self.element_finder.find_all(selector, timeout=timeout)
            return elements
        if action == "wait_for_any":
            elements = self._poll_find_all(selector, timeout=timeout)
            return elements
        if action == "tap_all":
            elements = self.element_finder.find_all(selector, timeout=timeout)
            results = []
            for element in elements:
                element.click()
                results.append(self._extract_text(element))
            return results
        if action == "return":
            return_value = step.get("value")
            if return_value is None:
                return_value = step.get("message")
            raise FlowReturn(self._resolve_data(return_value))
        if action == "log":
            message = step.get("message") or ""
            message = self._resolve_text(message)
            logger.info(message)
            return message

        raise ValueError(f"Unsupported flow action: {action}")

    def _poll_find_all(self, selector: Dict[str, Any], timeout: int = 15):
        start = time.time()
        while True:
            try:
                elements = self.element_finder.find_all(selector, timeout=1)
            except Exception:
                elements = []
            if elements:
                return elements
            if time.time() - start >= timeout:
                return []
            time.sleep(0.5)

    def _perform_if(self, step: Dict[str, Any]) -> Dict[str, Any]:
        condition = step.get("condicao") or {}
        timeout = step.get("timeout", 10)
        matched = self._condition_met(condition, timeout=timeout)
        branch = step.get("then") if matched else step.get("else")

        result = {
            "matched": matched,
            "steps": self._execute_steps(branch or [], catch_return=False),
        }
        return result

    def _perform_loop(self, step: Dict[str, Any]) -> Dict[str, Any]:
        over = step.get("over")
        if isinstance(over, str):
            over = self._resolve_text(over)

        if not isinstance(over, list):
            raise ValueError("Loop action requires 'over' to be a list or a variable reference to a list")

        var_name = step.get("var_name") or "item"
        back_after_each = step.get("back_after_each", False)
        iterations = []
        previous_value = self.context.get(var_name, None)

        try:
            for item in over:
                self.context[var_name] = item
                iteration_result = self._execute_steps(step.get("steps", []), catch_return=False)
                iterations.append({"value": item, "result": iteration_result})
                if back_after_each:
                    self.device.press("back")
        except FlowReturn:
            if previous_value is None:
                self.context.pop(var_name, None)
            else:
                self.context[var_name] = previous_value
            raise

        if previous_value is None:
            self.context.pop(var_name, None)
        else:
            self.context[var_name] = previous_value

        return {"iterations": iterations}

    def _execute_step(self, step: Dict[str, Any]) -> Any:
        action = step.get("action")
        if action == "if":
            return self._perform_if(step)
        if action == "loop":
            return self._perform_loop(step)
        return self._perform_action(step)

    def _execute_steps(self, steps: List[Dict[str, Any]], catch_return: bool = True) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for step in steps:
            step = normalize_step(step)
            step["selector"] = self._resolve_data(step.get("selector", {}))
            step["value"] = self._resolve_data(step.get("value"))
            step["message"] = self._resolve_data(step.get("message"))
            step["condicao"] = self._resolve_data(step.get("condicao"))
            step["over"] = self._resolve_data(step.get("over"))
            step["steps"] = [normalize_step(s) for s in step.get("steps", [])]
            step["then"] = [normalize_step(s) for s in step.get("then", [])]
            step["else"] = [normalize_step(s) for s in step.get("else", [])]
            try:
                result = self._execute_step(step)
            except FlowReturn as flow_return:
                if catch_return:
                    return [
                        {"step": step, "result": "return", "value": flow_return.value}
                    ]
                raise
            except Exception as error:
                logger.warning("Step failed '%s': %s", step.get("name") or step.get("action"), error)
                self._handle_failure(step.get("on_failure"))
                if step.get("continue_on_failure"):
                    results.append({"step": step, "error": str(error)})
                    continue
                raise
            results.append({"step": step, "result": result})
        return results

    def _run_launch(self, launch: Dict[str, Any]) -> None:
        if not self.flow_package:
            return
        self.device.app_start(self.flow_package)
        wait_identifier = launch.get("wait_identifier")
        timeout = launch.get("timeout", 10)
        if wait_identifier:
            # wait_identifier can be a string (search by containsText) or a selector dict
            if isinstance(wait_identifier, dict):
                self.element_finder.wait_for(wait_identifier, timeout=timeout)
            else:
                self.element_finder.wait_for({"containsText": wait_identifier}, timeout=timeout)
            return

        # If no explicit wait identifier, try to find a first 'wait' step in the flow
        # stored in the flow_path context: the caller should supply steps via flow
        # We try to be forgiving: check context for a reserved key `_first_wait_step_selector`
        first_wait = None
        if isinstance(self.context.get("_first_wait_step_selector"), dict):
            first_wait = self.context.get("_first_wait_step_selector")

        if first_wait:
            self.element_finder.wait_for(first_wait, timeout=timeout)

    def run_flow(self, flow: Dict[str, Any]) -> List[Dict[str, Any]]:
        self.context = flow.get("variables", {}).copy() if isinstance(flow.get("variables"), dict) else {}
        self.flow_package = flow.get("package")
        self.flow_path = Path(flow.get("_flow_path")) if flow.get("_flow_path") else None
        self._load_file_variables(flow)

        launch = flow.get("launch")
        # precompute first wait selector from flow steps to assist launch waiting
        try:
            steps = get_steps(flow)
            for s in steps:
                if s.get("action") in ("wait", "wait_for"):
                    # store resolved selector in context for _run_launch
                    sel = s.get("selector") or s.get("target") or {}
                    self.context["_first_wait_step_selector"] = sel
                    break
        except Exception:
            pass

        if launch:
            self._run_launch(launch)
        elif self.flow_package and not any(step.get("action") == "launch_app" for step in get_steps(flow)):
            self.device.app_start(self.flow_package)

        return self._execute_steps(get_steps(flow))
