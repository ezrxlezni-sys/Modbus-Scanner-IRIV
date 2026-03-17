# scanner.py
"""
Scanner logic for Modbus RTU device detection.

This file is platform-independent.
It does not care whether the backend is:
- IRIV IO Controller
- IRIV PiControl

It only expects a client object with these methods:
- set_baudrate(baudrate)
- read_holding_registers(slave_addr, starting_addr, register_qty, signed)
- read_input_registers(slave_addr, starting_addr, register_qty, signed)   # optional
- close()   # optional
"""

import time

from config import (
    BAUDRATES,
    SLAVE_ID_START,
    SLAVE_ID_END,
    REGISTER_ADDRESS,
    REGISTER_QUANTITY,
    SIGNED,
    TRY_HOLDING_REGISTERS,
    TRY_INPUT_REGISTERS,
    SCAN_DELAY,
    SHOW_ERROR_DETAILS,
    STOP_AFTER_FIRST_FOUND,
)


def print_banner():
    print("=" * 50)
    print("           MODBUS RTU SCANNER START")
    print("=" * 50)


def print_footer():
    print("=" * 50)
    print("            MODBUS RTU SCANNER END")
    print("=" * 50)


def print_found(device):
    print("    FOUND device!")
    print(f"    Baudrate      : {device['baudrate']}")
    print(f"    Slave ID      : {device['slave_id']}")
    print(f"    Register type : {device['register_type']}")
    print(f"    Data          : {device['data']}")


def print_summary(found_devices):
    print("\n===== SCAN SUMMARY =====")

    if not found_devices:
        print("No Modbus devices found.")
        return

    for index, dev in enumerate(found_devices, start=1):
        print(
            f"{index}. "
            f"Slave ID={dev['slave_id']}, "
            f"Baudrate={dev['baudrate']}, "
            f"Type={dev['register_type']}, "
            f"Data={dev['data']}"
        )


def is_duplicate(found_devices, new_device):
    for dev in found_devices:
        if (
            dev["baudrate"] == new_device["baudrate"]
            and dev["slave_id"] == new_device["slave_id"]
            and dev["register_type"] == new_device["register_type"]
        ):
            return True
    return False


def try_holding_registers(client, baudrate, slave_id):
    data = client.read_holding_registers(
        slave_addr=slave_id,
        starting_addr=REGISTER_ADDRESS,
        register_qty=REGISTER_QUANTITY,
        signed=SIGNED,
    )

    return {
        "baudrate": baudrate,
        "slave_id": slave_id,
        "register_type": "holding",
        "data": data,
    }


def try_input_registers(client, baudrate, slave_id):
    data = client.read_input_registers(
        slave_addr=slave_id,
        starting_addr=REGISTER_ADDRESS,
        register_qty=REGISTER_QUANTITY,
        signed=SIGNED,
    )

    return {
        "baudrate": baudrate,
        "slave_id": slave_id,
        "register_type": "input",
        "data": data,
    }


def scan_one_slave(client, baudrate, slave_id):
    """
    Try one slave ID using enabled register types.
    Returns a list of found device dictionaries.
    """
    results = []

    print(f"  Trying Slave ID: {slave_id}")

    if TRY_HOLDING_REGISTERS:
        try:
            device = try_holding_registers(client, baudrate, slave_id)
            print_found(device)
            results.append(device)
        except Exception as e:
            if SHOW_ERROR_DETAILS:
                print(f"    Holding register failed: {e}")
            else:
                print("    Holding register failed")

    if TRY_INPUT_REGISTERS:
        try:
            device = try_input_registers(client, baudrate, slave_id)
            print_found(device)
            results.append(device)
        except Exception as e:
            if SHOW_ERROR_DETAILS:
                print(f"    Input register failed  : {e}")
            else:
                print("    Input register failed")

    if not results and not SHOW_ERROR_DETAILS:
        print("    No response")

    return results


def scan_modbus(client):
    """
    Main scan function.

    client must provide:
    - set_baudrate(baudrate)
    - read_holding_registers(...)
    - read_input_registers(...)   [if TRY_INPUT_REGISTERS = True]
    - close()                     [optional]
    """
    found_devices = []

    print_banner()

    try:
        for baudrate in BAUDRATES:
            print(f"\nTesting Baudrate: {baudrate}")

            try:
                client.set_baudrate(baudrate)
            except Exception as e:
                print(f"Failed to set baudrate {baudrate}: {e}")
                continue

            for slave_id in range(SLAVE_ID_START, SLAVE_ID_END + 1):
                devices = scan_one_slave(client, baudrate, slave_id)

                for device in devices:
                    if not is_duplicate(found_devices, device):
                        found_devices.append(device)

                        if STOP_AFTER_FIRST_FOUND:
                            print("\nStop-after-first-found is enabled.")
                            print_summary(found_devices)
                            print_footer()
                            return found_devices

                time.sleep(SCAN_DELAY)

    finally:
        if hasattr(client, "close"):
            try:
                client.close()
            except Exception as e:
                if SHOW_ERROR_DETAILS:
                    print(f"Client close warning: {e}")

    print_summary(found_devices)
    print_footer()

    return found_devices
