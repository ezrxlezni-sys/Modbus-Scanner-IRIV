# backends/picontrol_client.py
"""
PiControl backend for Modbus scanner.

This backend is for Linux Python on IRIV PiControl.
It does not use the IOC MicroPython/CircuitPython Modbus library.

Requirements:
    pip install pyserial
"""

import struct
import time

import serial

from config import (
    SERIAL_PORT,
    BYTESIZE,
    PARITY,
    STOPBITS,
    TIMEOUT,
    SHOW_ERROR_DETAILS,
)


class PiControlModbusClient:
    def __init__(self, port=SERIAL_PORT):
        self.port_name = port
        self.ser = None
        self.current_baudrate = None

    def set_baudrate(self, baudrate):
        """
        Open or reopen the serial port at a new baudrate.
        """
        if self.current_baudrate == baudrate and self.ser is not None and self.ser.is_open:
            return

        self.close()

        try:
            self.ser = serial.Serial(
                port=self.port_name,
                baudrate=baudrate,
                bytesize=self._convert_bytesize(BYTESIZE),
                parity=self._convert_parity(PARITY),
                stopbits=self._convert_stopbits(STOPBITS),
                timeout=TIMEOUT,
            )
            self.current_baudrate = baudrate

            # Clear any old buffered data
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()

        except Exception as e:
            self.ser = None
            self.current_baudrate = None
            raise RuntimeError(
                f"Failed to open serial port '{self.port_name}' at baudrate {baudrate}: {e}"
            )

    def read_holding_registers(self, slave_addr, starting_addr, register_qty, signed=False):
        """
        Modbus function 0x03
        """
        self._ensure_ready()
        return self._read_registers(
            slave_addr=slave_addr,
            function_code=0x03,
            starting_addr=starting_addr,
            register_qty=register_qty,
            signed=signed,
        )

    def read_input_registers(self, slave_addr, starting_addr, register_qty, signed=False):
        """
        Modbus function 0x04
        """
        self._ensure_ready()
        return self._read_registers(
            slave_addr=slave_addr,
            function_code=0x04,
            starting_addr=starting_addr,
            register_qty=register_qty,
            signed=signed,
        )

    def close(self):
        if self.ser is not None:
            try:
                if self.ser.is_open:
                    self.ser.close()
            except Exception as e:
                if SHOW_ERROR_DETAILS:
                    print(f"PiControl serial close warning: {e}")
            finally:
                self.ser = None
                self.current_baudrate = None

    def _read_registers(self, slave_addr, function_code, starting_addr, register_qty, signed):
        """
        Send Modbus RTU read request and parse response.
        """
        request = self._build_read_request(
            slave_addr=slave_addr,
            function_code=function_code,
            starting_addr=starting_addr,
            register_qty=register_qty,
        )

        # Clear buffers before request
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()

        # Send request
        self.ser.write(request)
        self.ser.flush()

        # Small delay so slave has time to reply
        time.sleep(0.05)

        # Expected normal response length:
        # slave(1) + function(1) + bytecount(1) + data(2*N) + crc(2)
        expected_length = 5 + (2 * register_qty)

        response = self.ser.read(expected_length)

        if len(response) == 0:
            raise RuntimeError("no data received from slave")

        # Check exception response first:
        # slave + (function|0x80) + exception_code + crc_lo + crc_hi
        if len(response) >= 5 and response[1] == (function_code | 0x80):
            self._validate_crc(response[:5])
            exception_code = response[2]
            raise RuntimeError(f"slave returned exception code: {exception_code}")

        if len(response) < expected_length:
            raise RuntimeError(
                f"incomplete response: expected {expected_length} bytes, got {len(response)}"
            )

        self._validate_crc(response)

        response_slave = response[0]
        response_function = response[1]
        byte_count = response[2]

        if response_slave != slave_addr:
            raise RuntimeError(
                f"wrong slave address in response: expected {slave_addr}, got {response_slave}"
            )

        if response_function != function_code:
            raise RuntimeError(
                f"wrong function code in response: expected {function_code}, got {response_function}"
            )

        if byte_count != (register_qty * 2):
            raise RuntimeError(
                f"wrong byte count in response: expected {register_qty * 2}, got {byte_count}"
            )

        data_bytes = response[3:3 + byte_count]

        values = []
        for i in range(0, len(data_bytes), 2):
            raw_value = struct.unpack(">H", data_bytes[i:i + 2])[0]

            if signed and raw_value >= 0x8000:
                raw_value -= 0x10000

            values.append(raw_value)

        return values

    def _build_read_request(self, slave_addr, function_code, starting_addr, register_qty):
        """
        Build Modbus RTU request:
        [slave][function][start_hi][start_lo][qty_hi][qty_lo][crc_lo][crc_hi]
        """
        payload = struct.pack(">BBHH", slave_addr, function_code, starting_addr, register_qty)
        crc = self._crc16(payload)
        return payload + struct.pack("<H", crc)

    def _validate_crc(self, frame):
        """
        Validate Modbus RTU CRC.
        """
        if len(frame) < 3:
            raise RuntimeError("response too short for CRC check")

        data = frame[:-2]
        received_crc = struct.unpack("<H", frame[-2:])[0]
        calculated_crc = self._crc16(data)

        if received_crc != calculated_crc:
            raise RuntimeError(
                f"invalid response CRC: received 0x{received_crc:04X}, calculated 0x{calculated_crc:04X}"
            )

    @staticmethod
    def _crc16(data):
        """
        Standard Modbus RTU CRC16.
        """
        crc = 0xFFFF

        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1

        return crc & 0xFFFF

    def _ensure_ready(self):
        if self.ser is None or not self.ser.is_open:
            raise RuntimeError("PiControl serial client is not initialized. Call set_baudrate() first.")

    @staticmethod
    def _convert_bytesize(value):
        if value == 8:
            return serial.EIGHTBITS
        if value == 7:
            return serial.SEVENBITS
        raise ValueError(f"Unsupported bytesize: {value}")

    @staticmethod
    def _convert_parity(value):
        if value == "N":
            return serial.PARITY_NONE
        if value == "E":
            return serial.PARITY_EVEN
        if value == "O":
            return serial.PARITY_ODD
        raise ValueError(f"Unsupported parity: {value}")

    @staticmethod
    def _convert_stopbits(value):
        if value == 1:
            return serial.STOPBITS_ONE
        if value == 2:
            return serial.STOPBITS_TWO
        raise ValueError(f"Unsupported stopbits: {value}")