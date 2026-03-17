# config.py
"""
Project configuration for Modbus Configuration Tool.

This file is meant to be easy to edit.
Change values here without touching the scanner logic.
"""

# Select platform:
# "ioc"       -> IRIV IO Controller using the current MicroPython-style library
# "picontrol" -> IRIV PiControl using Linux serial port
PLATFORM = "picontrol"

# PiControl serial port
# Change this later if your actual RS485 device is different
SERIAL_PORT = "/dev/ttyACM0"

# Common Modbus communication settings
BAUDRATES = [4800, 9600, 19200, 38400]
SLAVE_ID_START = 1
SLAVE_ID_END = 10

# Register scan settings
REGISTER_ADDRESS = 0
REGISTER_QUANTITY = 1
SIGNED = False

# Try more than one Modbus register type
TRY_HOLDING_REGISTERS = True
TRY_INPUT_REGISTERS = True

# Scanner behavior
SCAN_DELAY = 0.1
SHOW_ERROR_DETAILS = True
STOP_AFTER_FIRST_FOUND = False

# Serial defaults for PiControl/Linux
BYTESIZE = 8
PARITY = "N"
STOPBITS = 1
TIMEOUT = 0.3
