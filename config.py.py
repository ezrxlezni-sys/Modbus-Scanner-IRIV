#!/usr/bin/env python3
"""
config.py
Central configuration file for Modbus scanner project.

Purpose:
- keep settings in one place
- easier for beginner to modify
- can support both PiControl and IO Controller later
"""


# ==========================================================
# PLATFORM SELECTION
# ==========================================================
# Change this depending on which hardware you use:
#   "picontrol"  -> IRIV PiControl (Linux, /dev/ttyACM0)
#   "ioc"        -> IRIV IO Controller / MicroPython style
PLATFORM = "picontrol"


# ==========================================================
# SERIAL SETTINGS
# ==========================================================
SERIAL_PORT = "/dev/ttyACM0"

DEFAULT_DATABITS = 8
DEFAULT_STOPBITS = 1
DEFAULT_PARITY = "N"
DEFAULT_TIMEOUT = 0.5


# ==========================================================
# SCANNER SETTINGS
# ==========================================================
BAUDRATES = [4800, 9600, 19200, 38400, 57600, 115200]

SLAVE_ID_START = 1
SLAVE_ID_END = 247

REGISTER_ADDRESS = 0
REGISTER_QTY = 1
SIGNED = False


# ==========================================================
# TIMING SETTINGS
# ==========================================================
SCAN_DELAY = 0.05
BAUD_CHANGE_DELAY = 0.2


# ==========================================================
# ADVANCED OPTIONS
# ==========================================================
SHOW_NO_RESPONSE = True
STOP_AFTER_FIRST_FOUND = False


# ==========================================================
# HELPER FUNCTIONS
# ==========================================================
def get_slave_range():
    """
    Return Python range for slave ID scanning.
    """
    return range(SLAVE_ID_START, SLAVE_ID_END + 1)


def validate_config():
    """
    Basic config validation.
    Raise ValueError if configuration is not valid.
    """
    if PLATFORM not in ("picontrol", "ioc"):
        raise ValueError(
            f"Invalid PLATFORM: {PLATFORM}. Use 'picontrol' or 'ioc'."
        )

    if not isinstance(BAUDRATES, list) or len(BAUDRATES) == 0:
        raise ValueError("BAUDRATES must be a non-empty list.")

    if SLAVE_ID_START < 1 or SLAVE_ID_END > 247:
        raise ValueError("Slave ID range must be between 1 and 247.")

    if SLAVE_ID_START > SLAVE_ID_END:
        raise ValueError("SLAVE_ID_START must be <= SLAVE_ID_END.")

    if REGISTER_QTY < 1:
        raise ValueError("REGISTER_QTY must be at least 1.")

    if DEFAULT_DATABITS not in (5, 6, 7, 8):
        raise ValueError("DEFAULT_DATABITS must be 5, 6, 7, or 8.")

    if DEFAULT_STOPBITS not in (1, 2):
        raise ValueError("DEFAULT_STOPBITS must be 1 or 2.")

    if str(DEFAULT_PARITY).upper() not in ("N", "E", "O", "NONE", "EVEN", "ODD"):
        raise ValueError("DEFAULT_PARITY must be N, E, O, NONE, EVEN, or ODD.")

    if DEFAULT_TIMEOUT <= 0:
        raise ValueError("DEFAULT_TIMEOUT must be greater than 0.")

    if SCAN_DELAY < 0:
        raise ValueError("SCAN_DELAY cannot be negative.")

    if BAUD_CHANGE_DELAY < 0:
        raise ValueError("BAUD_CHANGE_DELAY cannot be negative.")


def print_config():
    """
    Print active configuration for debugging.
    """
    print("=" * 60)
    print(" Active Scanner Configuration")
    print("=" * 60)
    print(f"Platform           : {PLATFORM}")
    print(f"Serial port        : {SERIAL_PORT}")
    print(f"Baudrates          : {BAUDRATES}")
    print(f"Data bits          : {DEFAULT_DATABITS}")
    print(f"Stop bits          : {DEFAULT_STOPBITS}")
    print(f"Parity             : {DEFAULT_PARITY}")
    print(f"Timeout            : {DEFAULT_TIMEOUT}")
    print(f"Slave ID range     : {SLAVE_ID_START} to {SLAVE_ID_END}")
    print(f"Register address   : {REGISTER_ADDRESS}")
    print(f"Register quantity  : {REGISTER_QTY}")
    print(f"Signed             : {SIGNED}")
    print(f"Scan delay         : {SCAN_DELAY}")
    print(f"Baud change delay  : {BAUD_CHANGE_DELAY}")
    print(f"Show no response   : {SHOW_NO_RESPONSE}")
    print(f"Stop after found   : {STOP_AFTER_FIRST_FOUND}")
    print("=" * 60)