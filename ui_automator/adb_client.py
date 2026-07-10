import logging
from typing import Optional

logger = logging.getLogger(__name__)


class AdbDeviceConnector:
    def __init__(self, serial: Optional[str] = None, host: Optional[str] = None, port: int = 5555):
        self.serial = serial
        self.host = host
        self.port = port
        self.device = None

    def connect(self):
        """Connect to an Android device via ADB and UIAutomator2."""
        try:
            import uiautomator2 as u2
        except ImportError as exc:
            raise RuntimeError("uiautomator2 is not installed. Install it with 'pip install uiautomator2'.") from exc

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

        if hasattr(self.device, "healthcheck"):
            self.device.healthcheck()
        else:
            try:
                _ = self.device.info
            except Exception as exc:
                raise RuntimeError("Unable to verify UIAutomator2 device connection") from exc

        logger.info("Connected to device: %s", getattr(self.device, "serial", "unknown"))
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
