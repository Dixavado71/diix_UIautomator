import logging

import pytest
from ui_automator.action_runner import FlowRunner


class DummyDevice:
    def __init__(self):
        self.started = []

    def app_start(self, package):
        self.started.append(package)


class DummyElement:
    def __init__(self, text="R$ 100"):
        self.text = text
        self.exists_called = False

    def exists(self, timeout=0):
        self.exists_called = True
        return True

    def click(self):
        return True

    def set_text(self, text):
        self.text = text
        return True

    @property
    def info(self):
        return {"text": self.text}


class DummyFinder:
    def __init__(self, element):
        self.element = element

    def wait_for(self, selector, timeout=0):
        return self.element

    def find(self, selector, timeout=0):
        return self.element


class DummyDumpManager:
    def __init__(self):
        self.refreshed = False

    def refresh_dump(self):
        self.refreshed = True
        return {"hash": "abc"}


@pytest.fixture(autouse=True)
def patch_components(monkeypatch):
    from ui_automator import action_runner

    element = DummyElement()
    monkeypatch.setattr(action_runner, "ElementFinder", lambda device: DummyFinder(element))
    monkeypatch.setattr(action_runner, "DumpManager", lambda device: DummyDumpManager())
    return element


def test_flow_runner_launch_app(patch_components):
    device = DummyDevice()
    runner = FlowRunner(device)
    result = runner.run_flow({
        "package": "br.com.intermedium",
        "steps": [{"action": "launch_app", "package": "br.com.intermedium"}],
    })

    assert result[0]["result"]["launched"] == "br.com.intermedium"
    assert device.started == ["br.com.intermedium"]


def test_flow_runner_extract_and_log(patch_components):
    device = DummyDevice()
    runner = FlowRunner(device)
    result = runner.run_flow({
        "variables": {"saldo": "R$ 100"},
        "steps": [
            {"action": "extract", "target": {"texto_contem": "R$"}, "save_as": "saldo"},
            {"action": "log", "message": "Saldo: $saldo"},
        ],
    })

    assert result[0]["result"] == "R$ 100"
    assert "Saldo: R$ 100" in result[1]["result"] or result[1]["result"] == "Saldo: R$ 100"
