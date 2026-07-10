import argparse
import json
import logging
from pathlib import Path

from .adb_client import AdbDeviceConnector
from .flow_loader import load_flow
from .action_runner import FlowRunner

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Run an Android automation flow using UIAutomator2.")
    parser.add_argument("--flow", required=True, help="Path to the JSON flow file")
    parser.add_argument("--serial", help="Android device serial to connect")
    parser.add_argument("--host", help="Android device host for TCP connection")
    parser.add_argument("--port", type=int, default=5555, help="Port for TCP connection")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    connector = AdbDeviceConnector(serial=args.serial, host=args.host, port=args.port)
    device = connector.connect()
    flow = load_flow(args.flow)

    runner = FlowRunner(device)
    results = runner.run_flow(flow)

    output_path = Path(args.flow).with_suffix(".result.json")
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, ensure_ascii=False)

    logger.info("Flow execution finished. Results saved to %s", output_path)


if __name__ == "__main__":
    main()
