#!/usr/bin/env python3
"""
main_picontrol.py
Modbus RTU scanner for IRIV PiControl.
"""

import time
import config
from lib.umodbus.serial_linux import Serial as ModbusRTUMaster


def create_master(baudrate: int) -> ModbusRTUMaster:
    return ModbusRTUMaster(
        port=config.SERIAL_PORT,
        baudrate=baudrate,
        data_bits=config.DEFAULT_DATABITS,
        stop_bits=config.DEFAULT_STOPBITS,
        parity=config.DEFAULT_PARITY,
        timeout=config.DEFAULT_TIMEOUT,
    )


def try_read_register(host: ModbusRTUMaster, slave_id: int):
    try:
        data = host.read_holding_registers(
            slave_addr=slave_id,
            starting_addr=config.REGISTER_ADDRESS,
            register_qty=config.REGISTER_QTY,
            signed=config.SIGNED,
        )
        return True, data
    except Exception as exc:
        return False, str(exc)


def scan_modbus():
    found_devices = []
    host = None

    config.validate_config()
    config.print_config()

    for baud in config.BAUDRATES:
        print(f"\n[INFO] Testing baudrate: {baud}")

        if host is not None:
            try:
                host.close()
                print("[DEBUG] Previous serial port closed")
            except Exception as exc:
                print(f"[WARN] Failed to close previous serial: {exc}")

        try:
            host = create_master(baud)
            print(f"[OK] Opened {config.SERIAL_PORT} at {baud} baud")
        except Exception as exc:
            print(f"[ERROR] Cannot open serial port at {baud} baud: {exc}")
            continue

        time.sleep(config.BAUD_CHANGE_DELAY)

        for slave_id in config.get_slave_range():
            print(f"  -> Trying Slave ID {slave_id:03d}", end="")

            success, result = try_read_register(host, slave_id)

            if success:
                print("  [FOUND]")
                print(f"     Baudrate : {baud}")
                print(f"     Slave ID : {slave_id}")
                print(f"     Data     : {result}")

                found_devices.append({
                    "baudrate": baud,
                    "slave_id": slave_id,
                    "data": result,
                })

                if config.STOP_AFTER_FIRST_FOUND:
                    print("\n[INFO] Stop after first found is enabled.")
                    if host is not None:
                        try:
                            host.close()
                        except Exception:
                            pass
                    return found_devices

            else:
                if config.SHOW_NO_RESPONSE:
                    print(f"  [NO] {result}")
                else:
                    print("")

            time.sleep(config.SCAN_DELAY)

    if host is not None:
        try:
            host.close()
        except Exception:
            pass

    print("\n" + "=" * 60)
    print(" Scan Finished")
    print("=" * 60)

    if found_devices:
        print(f"Total devices found: {len(found_devices)}")
        for i, dev in enumerate(found_devices, start=1):
            print(
                f"{i}. Slave ID={dev['slave_id']}, "
                f"Baudrate={dev['baudrate']}, "
                f"Data={dev['data']}"
            )
    else:
        print("No Modbus device found.")

    print("=" * 60)
    return found_devices


if __name__ == "__main__":
    scan_modbus()