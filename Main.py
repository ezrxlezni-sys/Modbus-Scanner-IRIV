# main.py
"""
Main entry point for Modbus Configuration Tool.
"""

from config import PLATFORM
from scanner import scan_modbus


def create_client():
    """
    Select backend based on PLATFORM in config.py
    """
    if PLATFORM == "ioc":
        from backends.ioc_client import IOCModbusClient
        return IOCModbusClient()

    if PLATFORM == "picontrol":
        from backends.picontrol_client import PiControlModbusClient
        return PiControlModbusClient()

    raise ValueError(
        f"Invalid PLATFORM '{PLATFORM}'. Use 'ioc' or 'picontrol'."
    )


def main():
    print(f"Selected platform: {PLATFORM}")

    client = create_client()
    found_devices = scan_modbus(client)

    print("\nProgram finished.")
    print(f"Total devices found: {len(found_devices)}")


if __name__ == "__main__":
    main()
