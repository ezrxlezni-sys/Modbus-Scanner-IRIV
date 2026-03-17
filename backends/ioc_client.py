# backends/ioc_client.py
"""
IOC backend for Modbus scanner.

This backend uses the existing MicroPython/CircuitPython-style Modbus library
that works with:
- board.TX
- board.RX
- umodbus.serial.Serial

Use this backend only on IRIV IO Controller.
"""

import board
from umodbus.serial import Serial as ModbusRTUMaster

from config import (
    BYTESIZE,
    PARITY,
    STOPBITS,
    TIMEOUT,
    SHOW_ERROR_DETAILS,
)


class IOCModbusClient:
    def __init__(self):
        self.host = None
        self.current_baudrate = None

    def set_baudrate(self, baudrate):
        """
        Recreate the UART/Modbus master when baudrate changes.
        """
        if self.current_baudrate == baudrate and self.host is not None:
            return

        self.close()

        try:
            self.host = ModbusRTUMaster(
                tx_pin=board.TX,
                rx_pin=board.RX,
                baudrate=baudrate,
                data_bits=BYTESIZE,
                stop_bits=STOPBITS,
                parity=self._convert_parity(PARITY),
            )
            self.current_baudrate = baudrate

        except Exception as e:
            self.host = None
            self.current_baudrate = None
            raise RuntimeError(f"Failed to create IOC Modbus client: {e}")

    def read_holding_registers(self, slave_addr, starting_addr, register_qty, signed=False):
        """
        Read holding registers through the IOC Modbus library.
        """
        self._ensure_ready()

        try:
            return self.host.read_holding_registers(
                slave_addr=slave_addr,
                starting_addr=starting_addr,
                register_qty=register_qty,
                signed=signed,
            )
        except Exception as e:
            raise RuntimeError(f"holding register read failed: {e}")

    def read_input_registers(self, slave_addr, starting_addr, register_qty, signed=False):
        """
        Read input registers through the IOC Modbus library.
        """
        self._ensure_ready()

        try:
            return self.host.read_input_registers(
                slave_addr=slave_addr,
                starting_addr=starting_addr,
                register_qty=register_qty,
                signed=signed,
            )
        except Exception as e:
            raise RuntimeError(f"input register read failed: {e}")

    def close(self):
        """
        Safely close/deinitialize UART.
        """
        if self.host is None:
            return

        try:
            # The current library exposes the UART object as host._uart,
            # and your old code already used host._uart.deinit().
            self.host._uart.deinit()
        except Exception as e:
            if SHOW_ERROR_DETAILS:
                print(f"IOC UART close warning: {e}")
        finally:
            self.host = None
            self.current_baudrate = None

    def _ensure_ready(self):
        if self.host is None:
            raise RuntimeError("IOC Modbus client is not initialized. Call set_baudrate() first.")

    @staticmethod
    def _convert_parity(parity_value):
        """
        Convert config parity string to library-compatible value.

        Current config uses:
        - 'N' = None
        - 'E' = 0
        - 'O' = 1

        If your IOC UART library expects different parity values later,
        change only this function.
        """
        if parity_value == "N":
            return None
        if parity_value == "E":
            return 0
        if parity_value == "O":
            return 1

        raise ValueError(f"Unsupported parity value: {parity_value}")