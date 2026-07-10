import logging
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

    def find(self, selector: Dict[str, Any], timeout: int = 10):
        """Find an element using a selector dictionary with dynamic fallback."""
        if not selector:
            raise ValueError("Selector data is required")

        selector = {k: v for k, v in selector.items() if v is not None}
        logger.debug("Finding element with selector %s", selector)

        exact_keys = {k: selector[k] for k in selector if k in {"resourceId", "className", "text", "description"}}
        if exact_keys:
            ui_obj = self.device(**exact_keys)
            if ui_obj.exists(timeout=timeout):
                logger.info("Found element by exact selector %s", exact_keys)
                return ui_obj

        fallback = self._fallback_selector(selector)
        if fallback and fallback.exists(timeout=timeout):
            logger.info("Found element by fallback selector %s", selector)
            return fallback

        raise RuntimeError(f"Element not found for selector: {selector}")

    def _fallback_selector(self, selector: Dict[str, Any]):
        if "className" in selector and ("containsText" not in selector and "containsDescription" not in selector):
            return self.device.xpath(f"//{selector['className']}")

        conditions = []
        if "containsText" in selector:
            value = self._escape_value(selector["containsText"])
            conditions.append(f"contains(@text, {value}) or contains(@content-desc, {value})")
        if "containsDescription" in selector:
            value = self._escape_value(selector["containsDescription"])
            conditions.append(f"contains(@content-desc, {value}) or contains(@text, {value})")
        if "text" in selector:
            value = self._escape_value(selector["text"])
            conditions.append(f"@text={value} or @content-desc={value}")
        if "description" in selector:
            value = self._escape_value(selector["description"])
            conditions.append(f"@content-desc={value} or @text={value}")

        if not conditions:
            return None

        xpath = "//*[(" + " or ".join(conditions) + ")]"
        if "className" in selector:
            xpath = f"//{selector['className']}[(" + " or ".join(conditions) + ")]"

        return self.device.xpath(xpath)

    def wait_for(self, selector: Dict[str, Any], timeout: int = 20):
        return self.find(selector, timeout=timeout)
