import sys

import pytest

from ui_automator.adb_client import AdbDeviceConnector


class DummyUiaDevice:
    def __init__(self):
        self.serial = "TEST123"
        self.info = {"packageName": "com.example", "currentPackageName": "com.example/.Main"}
        self.healthcheck_called = False

    def healthcheck(self):
        self.healthcheck_called = True


class DummyU2Module:
    def __init__(self, device):
        self._device = device

    def connect(self, serial=None):
        return self._device

    def connect_usb(self):
        return self._device


@pytest.fixture(autouse=True)
def patch_uiautomator2(monkeypatch):
    dummy_device = DummyUiaDevice()
    dummy_module = DummyU2Module(dummy_device)
    monkeypatch.setitem(sys.modules, "uiautomator2", dummy_module)
    yield


def test_connect_usb(monkeypatch):
    device = DummyUiaDevice()
    connector = AdbDeviceConnector()

    class DummyU2ModuleOverride:
        def connect_usb(self):
            return device

    monkeypatch.setitem(sys.modules, "uiautomator2", DummyU2ModuleOverride())

    connected = connector.connect()
    assert connected is device
    assert connected.healthcheck_called
