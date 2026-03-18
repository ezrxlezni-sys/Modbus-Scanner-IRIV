"""
main_ioc.py
Modbus RTU scanner for IRIV IO Controller / MicroPython-style environment.
"""

import time
import board
import config
from lib.umodbus.serial import Serial as ModbusRTUMaster


def sleep_ms(ms: int):
    """
    Small compatibility helper.
    """
    try:
        time.sleep_ms(ms)
    except AttributeError:
        time.sleep(ms / 1000)


def print_ioc_header():
    print("=" * 60)
    print(" IRIV IO Controller Modbus Scanner")
    print("=" * 60)
    print(f"Platform           : {config.PLATFORM}")
    print(f"TX Pin             : board.TX")
    print(f"RX Pin             : board.RX")
    print(f"Baudrates          : {config.BAUDRATES}")
    print(f"Slave ID range     : {config.SLAVE_ID_START} to {config.SLAVE_ID_END}")
    print(f"Register address   : {config.REGISTER_ADDRESS}")
    print(f"Register quantity  : {config.REGISTER_QTY}")
    print(f"Signed             : {config.SIGNED}")
    print(f"Timeout            : library default / UART timing")
    print("=" * 60)


def create_master(baudrate: int) -> ModbusRTUMaster:
    """
    Create Modbus RTU master for IO Controller.
    """
    return ModbusRTUMaster(
        tx_pin=board.TX,
        rx_pin=board.RX,
        baudrate=baudrate,
        data_bits=config.DEFAULT_DATABITS,
        stop_bits=config.DEFAULT_STOPBITS,
        parity=None if str(config.DEFAULT_PARITY).upper() in ("N", "NONE") else config.DEFAULT_PARITY,
        de_not_re_pin=None,
    )


def try_read_register(host: ModbusRTUMaster, slave_id: int):
    """
    Try reading one holding register from one slave.
    """
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
    config.validate_config()
    print_ioc_header()

    for baud in config.BAUDRATES:
        print(f"\n[INFO] Testing baudrate: {baud}")

        try:
            host = create_master(baud)
            print(f"[OK] UART initialized at {baud} baud")
        except Exception as exc:
            print(f"[ERROR] Cannot initialize UART at {baud} baud: {exc}")
            continue

        sleep_ms(int(config.BAUD_CHANGE_DELAY * 1000))

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
                    print_summary(found_devices)
                    return found_devices
            else:
                if config.SHOW_NO_RESPONSE:
                    print(f"  [NO] {result}")
                else:
                    print("")

            sleep_ms(int(config.SCAN_DELAY * 1000))

    print_summary(found_devices)
    return found_devices


def print_summary(found_devices):
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


if __name__ == "__main__":
    scan_modbus()