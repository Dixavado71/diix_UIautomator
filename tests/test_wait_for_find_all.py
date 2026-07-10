import time

from ui_automator.action_runner import FlowRunner


class DummyDevice:
    pass


class TransientFinder:
    def __init__(self, element):
        self.element = element
        self.calls = 0

    def wait_for(self, selector, timeout=0):
        raise RuntimeError("no wait_for")

    def find(self, selector, timeout=0):
        raise RuntimeError("not used")

    def find_all(self, selector, timeout=0):
        # return empty list for first two calls, then return the element
        self.calls += 1
        if self.calls < 3:
            return []
        return [self.element]


class DummyElement:
    def __init__(self):
        self.clicked = False

    def click(self):
        self.clicked = True
        return True


class DummyDumpManager:
    def __init__(self, device):
        pass

    def refresh_dump(self):
        return {"hash": "abc"}


def test_wait_for_fallback_to_find_all(monkeypatch):
    from ui_automator import action_runner

    element = DummyElement()
    monkeypatch.setattr(action_runner, "ElementFinder", lambda device: TransientFinder(element))
    monkeypatch.setattr(action_runner, "DumpManager", lambda device: DummyDumpManager(device))

    runner = FlowRunner(DummyDevice())
    result = runner.run_flow({
        "steps": [
            {"action": "wait", "selector": {"text": "transient"}, "timeout": 3},
        ]
    })

    assert result[0]["result"] is element


def test_wait_for_any_returns_all(monkeypatch):
    from ui_automator import action_runner

    element = DummyElement()
    transient = TransientFinder(element)
    monkeypatch.setattr(action_runner, "ElementFinder", lambda device: transient)
    monkeypatch.setattr(action_runner, "DumpManager", lambda device: DummyDumpManager(device))

    runner = FlowRunner(DummyDevice())
    result = runner.run_flow({
        "steps": [
            {"action": "wait_any", "selector": {"text": "transient"}, "timeout": 3},
        ]
    })

    assert isinstance(result[0]["result"], list)
    assert result[0]["result"][0] is element
