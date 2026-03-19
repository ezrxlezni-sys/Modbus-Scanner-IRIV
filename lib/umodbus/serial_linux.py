#!/usr/bin/env python3
"""
Required:
    pip install pyserial
or:
    sudo apt install python3-serial
"""

import struct
import time

try:
    import serial as pyserial
except ImportError as exc:
    raise ImportError(
        "pyserial is required for serial_linux.py. "
        "Install with: pip install pyserial "
        "or sudo apt install python3-serial"
    ) from exc

from . import const as Const
from . import functions
from .common import Request, CommonModbusFunctions, ModbusException
from .modbus import Modbus
from .typing import List, Optional, Union


class ModbusRTU(Modbus):
    """
    Linux Modbus RTU client class for PiControl.

    Example:
        host = ModbusRTU(port='/dev/ttyACM0', baudrate=9600)
    """

    def __init__(
        self,
        port: str = "/dev/ttyACM0",
        addr: int = 1,
        baudrate: int = 9600,
        data_bits: int = 8,
        stop_bits: int = 1,
        parity: Optional[str] = "N",
        timeout: float = 1.0,
    ):
        super().__init__(
            Serial(
                port=port,
                baudrate=baudrate,
                data_bits=data_bits,
                stop_bits=stop_bits,
                parity=parity,
                timeout=timeout,
            ),
            [addr],
        )


class Serial(CommonModbusFunctions):
    """
    Linux serial interface for Modbus RTU.

    Keeps a similar role to your original Serial class,
    but uses pyserial instead of busio.UART.
    """

    def __init__(
        self,
        port: str = "/dev/ttyACM0",
        baudrate: int = 9600,
        data_bits: int = 8,
        stop_bits: int = 1,
        parity: Optional[str] = "N",
        timeout: float = 1.0,
    ):
        self.port = port
        self.baudrate = baudrate
        self.data_bits = data_bits
        self.stop_bits = stop_bits
        self.parity = self._normalize_parity(parity)
        self.timeout = timeout

        # timing of 1 character in microseconds
        # start bit + data bits + parity bit(if any) + stop bits
        parity_bits = 0 if self.parity == pyserial.PARITY_NONE else 1
        total_bits = 1 + data_bits + parity_bits + stop_bits
        self._t1char = int((total_bits / baudrate) * 1_000_000)

        # Modbus RTU inter-frame delay
        if baudrate <= 19200:
            self._inter_frame_delay = int(3.5 * self._t1char)
        else:
            self._inter_frame_delay = 1750

        self._uart = pyserial.Serial(
            port=self.port,
            baudrate=self.baudrate,
            bytesize=self._get_bytesize(data_bits),
            parity=self.parity,
            stopbits=self._get_stopbits(stop_bits),
            timeout=self.timeout,
            write_timeout=self.timeout,
        )

        # Clear old garbage data
        self.flush_input()

    def close(self) -> None:
        if self._uart and self._uart.is_open:
            self._uart.close()

    def flush_input(self) -> None:
        try:
            self._uart.reset_input_buffer()
        except Exception:
            pass

    def flush_output(self) -> None:
        try:
            self._uart.reset_output_buffer()
        except Exception:
            pass

    def reopen(
        self,
        baudrate: Optional[int] = None,
        data_bits: Optional[int] = None,
        stop_bits: Optional[int] = None,
        parity: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> None:
        """
        Reopen serial with new settings.
        Useful when scanning many baudrates.
        """
        if baudrate is not None:
            self.baudrate = baudrate
        if data_bits is not None:
            self.data_bits = data_bits
        if stop_bits is not None:
            self.stop_bits = stop_bits
        if parity is not None:
            self.parity = self._normalize_parity(parity)
        if timeout is not None:
            self.timeout = timeout

        self.close()

        parity_bits = 0 if self.parity == pyserial.PARITY_NONE else 1
        total_bits = 1 + self.data_bits + parity_bits + self.stop_bits
        self._t1char = int((total_bits / self.baudrate) * 1_000_000)

        if self.baudrate <= 19200:
            self._inter_frame_delay = int(3.5 * self._t1char)
        else:
            self._inter_frame_delay = 1750

        self._uart = pyserial.Serial(
            port=self.port,
            baudrate=self.baudrate,
            bytesize=self._get_bytesize(self.data_bits),
            parity=self.parity,
            stopbits=self._get_stopbits(self.stop_bits),
            timeout=self.timeout,
            write_timeout=self.timeout,
        )

        self.flush_input()

    def _normalize_parity(self, parity: Optional[str]) -> str:
        if parity is None:
            return pyserial.PARITY_NONE

        p = str(parity).upper()

        if p in ("N", "NONE"):
            return pyserial.PARITY_NONE
        if p in ("E", "EVEN"):
            return pyserial.PARITY_EVEN
        if p in ("O", "ODD"):
            return pyserial.PARITY_ODD

        raise ValueError(f"Unsupported parity: {parity}")

    def _get_bytesize(self, data_bits: int):
        mapping = {
            5: pyserial.FIVEBITS,
            6: pyserial.SIXBITS,
            7: pyserial.SEVENBITS,
            8: pyserial.EIGHTBITS,
        }
        if data_bits not in mapping:
            raise ValueError(f"Unsupported data bits: {data_bits}")
        return mapping[data_bits]

    def _get_stopbits(self, stop_bits: int):
        mapping = {
            1: pyserial.STOPBITS_ONE,
            2: pyserial.STOPBITS_TWO,
        }
        if stop_bits not in mapping:
            raise ValueError(f"Unsupported stop bits: {stop_bits}")
        return mapping[stop_bits]

    def _calculate_crc16(self, data: bytearray) -> bytes:
        crc = 0xFFFF

        for char in data:
            crc = (crc >> 8) ^ Const.CRC16_TABLE[((crc) ^ char) & 0xFF]

        return struct.pack("<H", crc)

    def _exit_read(self, response: bytearray) -> bool:
        response_len = len(response)

        if response_len >= 2 and response[1] >= Const.ERROR_BIAS:
            if response_len < Const.ERROR_RESP_LEN:
                return False
        elif response_len >= 3 and (
            Const.READ_COILS <= response[1] <= Const.READ_INPUT_REGISTER
        ):
            expected_len = (
                Const.RESPONSE_HDR_LENGTH + 1 + response[2] + Const.CRC_LENGTH
            )
            if response_len < expected_len:
                return False
        elif response_len < Const.FIXED_RESP_LEN:
            return False

        return True

    def _uart_read(self, response_timeout: Optional[float] = None) -> bytearray:
        """
        Read Modbus RTU response.
        First byte waits longer, next bytes use inter-frame timeout.
        """
        response = bytearray()

        original_timeout = self._uart.timeout
        first_timeout = self.timeout if response_timeout is None else response_timeout
        inter_byte_timeout = self._inter_frame_delay / 1_000_000.0

        try:
            self._uart.timeout = first_timeout

            first = self._uart.read(1)
            if not first:
                return response

            response.extend(first)

            while True:
                self._uart.timeout = inter_byte_timeout
                chunk = self._uart.read(1)
                if not chunk:
                    break
                response.extend(chunk)

                if self._exit_read(response):
                    # keep reading until timeout gap, in case more bytes still come
                    continue

            return response

        finally:
            self._uart.timeout = original_timeout

    def _uart_read_frame(self, timeout: Optional[float] = None) -> bytearray:
        """
        Read generic RTU frame for slave/server mode.
        """
        if timeout is None or timeout == 0:
            timeout = 2 * self._inter_frame_delay / 1_000_000.0

        return self._uart_read(response_timeout=timeout)

    def _send(self, modbus_pdu: bytes, slave_addr: int) -> None:
        """
        Send Modbus RTU ADU.
        PiControl RS485 direction is expected to be handled by hardware/driver.
        """
        modbus_adu = bytearray()
        modbus_adu.append(slave_addr)
        modbus_adu.extend(modbus_pdu)
        modbus_adu.extend(self._calculate_crc16(modbus_adu))

        self.flush_input()
        self._uart.write(modbus_adu)
        self._uart.flush()

        # small gap after send
        time.sleep(self._inter_frame_delay / 1_000_000.0)

    def _send_receive(
        self,
        modbus_pdu: bytes,
        slave_addr: int,
        count: bool,
    ) -> bytes:
        self.flush_input()
        self._send(modbus_pdu=modbus_pdu, slave_addr=slave_addr)

        response = self._uart_read()
        return self._validate_resp_hdr(
            response=response,
            slave_addr=slave_addr,
            function_code=modbus_pdu[0],
            count=count,
        )

    def _validate_resp_hdr(
        self,
        response: bytearray,
        slave_addr: int,
        function_code: int,
        count: bool,
    ) -> bytes:
        if len(response) == 0:
            raise OSError("no data received from slave")

        if len(response) < 5:
            raise OSError(f"incomplete response: {response.hex(' ')}")

        resp_crc = response[-Const.CRC_LENGTH:]
        expected_crc = self._calculate_crc16(response[:-Const.CRC_LENGTH])

        if (resp_crc[0] != expected_crc[0]) or (resp_crc[1] != expected_crc[1]):
            raise OSError(
                "invalid response CRC: "
                f"got={resp_crc.hex()} expected={expected_crc.hex()} raw={response.hex(' ')}"
            )

        if response[0] != slave_addr:
            raise ValueError(
                f"wrong slave address: got={response[0]} expected={slave_addr}"
            )

        if response[1] == (function_code + Const.ERROR_BIAS):
            raise ValueError(f"slave returned exception code: {response[2]}")

        hdr_length = (Const.RESPONSE_HDR_LENGTH + 1) if count else Const.RESPONSE_HDR_LENGTH
        return response[hdr_length:-Const.CRC_LENGTH]

    def send_response(
        self,
        slave_addr: int,
        function_code: int,
        request_register_addr: int,
        request_register_qty: int,
        request_data: list,
        values: Optional[list] = None,
        signed: bool = True,
    ) -> None:
        modbus_pdu = functions.response(
            function_code=function_code,
            request_register_addr=request_register_addr,
            request_register_qty=request_register_qty,
            request_data=request_data,
            value_list=values,
            signed=signed,
        )
        self._send(modbus_pdu=modbus_pdu, slave_addr=slave_addr)

    def send_exception_response(
        self,
        slave_addr: int,
        function_code: int,
        exception_code: int,
    ) -> None:
        modbus_pdu = functions.exception_response(
            function_code=function_code,
            exception_code=exception_code,
        )
        self._send(modbus_pdu=modbus_pdu, slave_addr=slave_addr)

    def get_request(
        self,
        unit_addr_list: List[int],
        timeout: Optional[float] = None,
    ) -> Union[Request, None]:
        req = self._uart_read_frame(timeout=timeout)

        if len(req) < 8:
            return None

        if req[0] not in unit_addr_list:
            return None

        req_crc = req[-Const.CRC_LENGTH:]
        req_no_crc = req[:-Const.CRC_LENGTH]
        expected_crc = self._calculate_crc16(req_no_crc)

        if (req_crc[0] != expected_crc[0]) or (req_crc[1] != expected_crc[1]):
            return None

        try:
            request = Request(interface=self, data=req_no_crc)
        except ModbusException as e:
            self.send_exception_response(
                slave_addr=req[0],
                function_code=e.function_code,
                exception_code=e.exception_code,
            )
            return None

        return request
