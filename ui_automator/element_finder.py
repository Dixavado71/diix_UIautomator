import logging
import time
from typing import Any, Dict

logger = logging.getLogger(__name__)


class ElementFinder:
    def __init__(self, device):
        self.device = device

    def _escape_value(self, value: str) -> str:
        if "'" in value and '"' in value:
            return value.replace("'", "\\'")
        if "'" in value:
            return f'"{value}"'
        return f"'{value}'"

    def _build_text_conditions(self, selector: Dict[str, Any]) -> list[str]:
        conditions = []
        for key in ("containsText", "containsDescription", "text", "description"):
            if key not in selector:
                continue
            values = selector[key] if isinstance(selector[key], list) else [selector[key]]
            for value in values:
                if not isinstance(value, str) or not value:
                    continue
                escaped = self._escape_value(value)
                if key == "containsText":
                    conditions.append(f"contains(@text, {escaped}) or contains(@content-desc, {escaped})")
                elif key == "containsDescription":
                    conditions.append(f"contains(@content-desc, {escaped}) or contains(@text, {escaped})")
                elif key == "text":
                    conditions.append(f"@text={escaped} or @content-desc={escaped}")
                elif key == "description":
                    conditions.append(f"@content-desc={escaped} or @text={escaped}")
        return conditions

    def _element_exists(self, element, timeout: int = 10) -> bool:
        exists_attr = getattr(element, "exists", None)
        if callable(exists_attr):
            try:
                return exists_attr(timeout=timeout)
            except TypeError:
                return bool(exists_attr)
        return bool(exists_attr)

    def _normalize_selector(self, selector: Any) -> Dict[str, Any]:
        if isinstance(selector, dict):
            return {k: v for k, v in selector.items() if v is not None}
        return {}

    def _wait_for_element(self, element_factory, selector: Dict[str, Any], timeout: int = 10) -> bool:
        start = time.time()

        while True:
            try:
                element = element_factory(selector)
            except Exception:
                element = None

            if element is None:
                if time.time() - start >= timeout:
                    return False
                time.sleep(0.5)
                continue

            wait_method = getattr(element, "wait", None)
            exists_attr = getattr(element, "exists", None)

            if callable(wait_method):
                try:
                    result = wait_method(timeout=timeout)
                    if bool(result):
                        return True
                except TypeError:
                    pass

            if callable(exists_attr):
                try:
                    if bool(exists_attr(timeout=timeout)):
                        return True
                except TypeError:
                    if bool(exists_attr):
                        return True

            elif bool(exists_attr):
                return True

            if time.time() - start >= timeout:
                return False

            time.sleep(0.5)

    def find(self, selector: Any, timeout: int = 10):
        """Find an element using a selector dictionary or a list of alternatives with dynamic fallback."""
        if not selector:
            raise ValueError("Selector data is required")

        selectors = selector if isinstance(selector, list) else [selector]
        for candidate in selectors:
            normalized = self._normalize_selector(candidate)
            if not normalized:
                continue
            logger.debug("Finding element with selector %s", normalized)

            fallback = None
            try:
                fallback = self._fallback_selector(normalized)
            except AttributeError:
                fallback = None

            if fallback and self._wait_for_element(lambda sel: self._fallback_selector(normalized), normalized, timeout=max(1, timeout // 2)):
                logger.info("Found element by fallback selector %s", normalized)
                return fallback

            exact_keys = {k: normalized[k] for k in normalized if k in {"resourceId", "className", "text", "description"}}
            if exact_keys:
                if self._wait_for_element(lambda sel: self.device(**exact_keys), normalized, timeout=timeout):
                    ui_obj = self.device(**exact_keys)
                    logger.info("Found element by exact selector %s", exact_keys)
                    return ui_obj

        raise RuntimeError(f"Element not found for selector: {selector}")

    def _fallback_selector(self, selector: Dict[str, Any]):
        if "className" in selector and ("containsText" not in selector and "containsDescription" not in selector):
            return self.device.xpath(f"//{selector['className']}")

        conditions = self._build_text_conditions(selector)

        if not conditions:
            return None

        xpath = "//*[(" + " or ".join(conditions) + ")]"
        if "className" in selector:
            xpath = f"//{selector['className']}[(" + " or ".join(conditions) + ")]"

        return self.device.xpath(xpath)

    def exists(self, selector: Dict[str, Any], timeout: int = 10) -> bool:
        try:
            self.find(selector, timeout=timeout)
            return True
        except RuntimeError:
            return False

    def find_all(self, selector: Any, timeout: int = 10):
        if not selector:
            raise ValueError("Selector data is required")

        selectors = selector if isinstance(selector, list) else [selector]
        for candidate in selectors:
            normalized = self._normalize_selector(candidate)
            if not normalized:
                continue
            logger.debug("Finding all elements with selector %s", normalized)

            exact_keys = {k: normalized[k] for k in normalized if k in {"resourceId", "className", "text", "description"}}
            if exact_keys:
                ui_obj = self.device(**exact_keys)
                try:
                    return ui_obj.all()
                except AttributeError:
                    if self._element_exists(ui_obj, timeout=timeout):
                        return [ui_obj]

            fallback = self._fallback_selector(normalized)
            if fallback:
                try:
                    return fallback.all()
                except AttributeError:
                    if self._element_exists(fallback, timeout=timeout):
                        return [fallback]

        raise RuntimeError(f"Elements not found for selector: {selector}")

    def wait_for(self, selector: Dict[str, Any], timeout: int = 20):
        return self.find(selector, timeout=timeout)
