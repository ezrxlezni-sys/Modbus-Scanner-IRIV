#!/usr/bin/env python3
"""
system.py
Main system launcher for Modbus Configuration Tool.

This file decides which platform logic to run:
- IRIV PiControl (Linux)
- IRIV IO Controller (MicroPython style)
"""

import sys
import config


def run_picontrol():
    print("\n[ SYSTEM ] Running PiControl Modbus Scanner...\n")
    import main_picontrol
    main_picontrol.scan_modbus()


def run_ioc():
    print("\n[ SYSTEM ] Running IO Controller Modbus Scanner...\n")
    import main_ioc
    main_ioc.scan_modbus()


def main():
    print("=" * 60)
    print(" IRIV Modbus Configuration Tool")
    print("=" * 60)

    try:
        config.validate_config()
    except Exception as e:
        print("[CONFIG ERROR]")
        print(e)
        return

    print(f"[ SYSTEM ] Selected Platform: {config.PLATFORM}")
    print("=" * 60)

    if config.PLATFORM.lower() == "picontrol":
        run_picontrol()

    elif config.PLATFORM.lower() == "ioc":
        run_ioc()

    else:
        print("[ERROR] Unknown PLATFORM in config.py")
        print("Use 'picontrol' or 'ioc'")


if __name__ == "__main__":
    main()