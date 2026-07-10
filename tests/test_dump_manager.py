from ui_automator.dump_manager import DumpManager


class DummyDevice:
    def __init__(self, xml, package_name="com.example", current_package_name="com.example/.Main"):
        self._xml = xml
        self.info = {
            "packageName": package_name,
            "currentPackageName": current_package_name,
        }
        self.dump_calls = 0

    def dump_hierarchy(self, compressed=False):
        self.dump_calls += 1
        return self._xml


def test_refresh_dump_caches_same_page():
    device = DummyDevice("<hierarchy></hierarchy>")
    manager = DumpManager(device)

    first = manager.refresh_dump()
    second = manager.refresh_dump()

    assert first["hash"] == second["hash"]
    assert first["xml"] == second["xml"]
    assert first["hash"] == manager.last_hash
    assert manager.last_hash in manager.cache


def test_get_cached_dump_uses_cache():
    device = DummyDevice("<hierarchy></hierarchy>")
    manager = DumpManager(device)

    manager.refresh_dump()
    result = manager.get_cached_dump()

    assert result["hash"] == manager.last_hash
    assert device.dump_calls == 1


def test_clear_cache_resets_state():
    device = DummyDevice("<hierarchy></hierarchy>")
    manager = DumpManager(device)

    manager.refresh_dump()
    manager.clear_cache()

    assert manager.last_hash is None
    assert manager.cache == {}
