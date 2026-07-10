import logging
from typing import Optional

import uiautomator2 as u2

logger = logging.getLogger(__name__)


class AdbDeviceConnector:
    def __init__(self, serial: Optional[str] = None, host: Optional[str] = None, port: int = 5555):
        self.serial = serial
        self.host = host
        self.port = port
        self.device = None

    def connect(self):
        """Connect to an Android device via ADB and UIAutomator2."""
        if self.serial:
            logger.info("Connecting to Android device by serial: %s", self.serial)
            self.device = u2.connect(self.serial)
        elif self.host:
            address = f"{self.host}:{self.port}"
            logger.info("Connecting to Android device by TCP: %s", address)
            self.device = u2.connect(address)
        else:
            logger.info("Connecting to Android device over USB")
            self.device = u2.connect_usb()

        self.device.healthcheck()
        logger.info("Connected to device: %s", self.device.serial)
        return self.device

    def set_fastinput(self):
        if self.device:
            self.device.service("fastinput", "enable")
            logger.debug("Enabled fastinput service on device")

    def install_app(self, apk_path: str):
        if self.device:
            self.device.app_install(apk_path)
            logger.info("Installed APK: %s", apk_path)

    def current_package(self) -> Optional[str]:
        return self.device.package_name if self.device else None
