import json
import sys
from pathlib import Path

from ui_automator import cli


class DummyDevice:
    pass


class DummyFlowRunner:
    def __init__(self, device):
        self.device = device

    def run_flow(self, flow):
        return [{"step": "dummy", "result": "ok"}]


class DummyConnector:
    def __init__(self, serial=None, host=None, port=None):
        self.serial = serial
        self.host = host
        self.port = port

    def connect(self):
        return DummyDevice()


def test_cli_writes_result_file(monkeypatch, tmp_path):
    flow_path = tmp_path / "example.json"
    flow_path.write_text(json.dumps({"steps": []}), encoding="utf-8")
    result_path = tmp_path / "out.result.json"

    monkeypatch.setattr(cli, "AdbDeviceConnector", DummyConnector)
    monkeypatch.setattr(cli, "FlowRunner", DummyFlowRunner)
    monkeypatch.setattr(sys, "argv", ["ui_automator.cli", "--flow", str(flow_path), "--result", str(result_path), "--debug"])

    cli.main()

    assert result_path.exists()
    assert json.loads(result_path.read_text(encoding="utf-8")) == [{"step": "dummy", "result": "ok"}]
