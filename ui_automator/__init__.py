"""diix_uiautomator package.

This package provides a modular Python framework for automating Android devices
using ADB and UIAutomator2.
"""

from .adb_client import AdbDeviceConnector
from .dump_manager import DumpManager
from .element_finder import ElementFinder
from .flow_loader import load_flow
from .action_runner import FlowRunner

__all__ = [
    "AdbDeviceConnector",
    "DumpManager",
    "ElementFinder",
    "load_flow",
    "FlowRunner",
]