import hashlib
import logging
import time
from typing import Any, Dict

logger = logging.getLogger(__name__)


class DumpManager:
    def __init__(self, device, cache: Dict[str, Dict[str, Any]] = None):
        self.device = device
        self.cache = cache or {}
        self.last_hash = None

    def _page_hash(self, xml_dump: str) -> str:
        return hashlib.sha256(xml_dump.encode("utf-8")).hexdigest()

    def refresh_dump(self) -> Dict[str, Any]:
        """Fetch the current UI dump and use a page hash to detect page changes."""
        xml_dump = self.device.dump_hierarchy(compressed=False)
        page_hash = self._page_hash(xml_dump)
        if page_hash == self.last_hash and page_hash in self.cache:
            logger.debug("Page hash unchanged: %s", page_hash)
            return self.cache[page_hash]

        dump_info = {
            "xml": xml_dump,
            "hash": page_hash,
            "timestamp": time.time(),
            "package": self.device.info.get("packageName"),
            "activity": self.device.info.get("currentPackageName"),
        }
        self.cache[page_hash] = dump_info
        self.last_hash = page_hash
        logger.info("Updated UI dump with hash %s", page_hash)
        return dump_info

    def get_cached_dump(self) -> Dict[str, Any]:
        if self.last_hash and self.last_hash in self.cache:
            return self.cache[self.last_hash]
        return self.refresh_dump()

    def clear_cache(self):
        self.cache.clear()
        self.last_hash = None
        logger.debug("Dump cache cleared")
